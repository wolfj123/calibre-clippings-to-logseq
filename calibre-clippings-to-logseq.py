from datetime import datetime
import sys
import os

class Clipping:
    def __init__(self, book_title, author, page, location_start, location_end, date, text, note):
        self.book_title = book_title
        self.author = author
        self.page = page
        self.location_start = location_start
        self.location_end = location_end
        self.date = date
        self.text = text
        self.note = note

def find_clipping_by_location_end(clippings, location_end):
    """Finds the first clipping in the list with a matching location_end.

    Args:
        clippings: A list of Clipping objects.
        location_end: The location_end value to search for.

    Returns:
        The first Clipping object that has the matching location_end, 
        or None if no clipping is found.
    """
    for clipping in clippings:
            if clipping.location_end == location_end:
                return clipping
    return None

def parse_highlight_file(filename):
    clippings = []
    current_book = None
    current_author = None
    with open(filename, 'r', encoding="utf-8") as file:
        for line in file:
            line = line.strip()  # Remove leading/trailing whitespaces

            # Extract book information (if present)
            if line and not line.startswith("-"):
                parts = line.split("(")
                current_book = parts[0].strip()
                # print(line)
                if len(parts) > 1:
                    current_author = parts[1].strip()[:-1]  # Remove closing parenthesis

            # Extract highlight data
            elif line.startswith("-"):
                # SKIP
                if "Bookmark" in line:
                    next_line = next(file).strip()
                    while next_line != "==========":
                        next_line = next(file).strip()
                    continue

                is_note = False
                data_parts = line.split("|")
                # SKIP
                if '-' in data_parts[0].split()[-1]:
                    next_line = next(file).strip()
                    while next_line != "==========":
                        next_line = next(file).strip()
                    continue

                page = int(data_parts[0].split()[-1])  # Extract page number
                if line.count('-') > 1:
                    print(line)
                    print(data_parts[1].split("location "))
                    location_data = data_parts[1].split("location ")[1].split("-")
                    location_start = int(location_data[0])
                    location_end = int(location_data[1])
                else:
                    is_note = True
                    print(line)
                    location_data = data_parts[1].split("location ")[1]
                    location_start = int(location_data)
                    location_end = location_start
                date_string = data_parts[2].split("Added on ")[-1].strip()
                date = datetime.strptime(date_string, "%A, %d %B %Y %H:%M:%S")

                # Extract text after separator
                text = ""
                next_line = next(file).strip()
                while next_line != "==========":
                    text += next_line + "\n"
                    next_line = next(file).strip()

                # Create clipping object and add to list
                if not is_note:
                    clipping = Clipping(current_book, current_author, page, location_start, location_end, date, text.strip(), "")
                    clippings.append(clipping)
                else:
                    relevant_clipping = find_clipping_by_location_end(clippings, location_end)
                    if relevant_clipping:
                        relevant_clipping.note = text.strip()
                    else:
                         print(location_end)

    return clippings

def separate_clippings_by_book(clippings):
    """Separates a list of clippings into a dictionary where keys are book titles and values are lists of clippings for that book.

    Args:
        clippings: A list of Clipping objects.

    Returns:
        A dictionary where keys are book titles and values are lists of Clipping objects for that book.
    """
    books = {}
    for clipping in clippings:
        book_title = clipping.book_title
        if book_title not in books:
            books[book_title] = []
        books[book_title].append(clipping)
    return books


# MAIN
args = sys.argv.copy()
args.pop(0)


# clippings_file_name, clippings_file_extension = os.path.splitext(args[0]) 
clippings_file_name, clippings_file_extension = os.path.splitext("clippings.txt") 
output_file_name = clippings_file_name + '_to_logseq.md'

clippings = parse_highlight_file(clippings_file_name + clippings_file_extension)

# for clipping in clippings:
#     print(f"Book: {clipping.book_title} by {clipping.author}")
#     print(f"Page: {clipping.page}, Location: {clipping.location_start} - {clipping.location_end}")
#     print(f"Date Added: {clipping.date}")
#     print(f"Text:\n{clipping.text}")
#     print(f"Note:\n{clipping.note}")
#     print("----------")

separated_by_book = separate_clippings_by_book(clippings)

sub_block_new_line = "\n\t\t  "
with open(output_file_name, 'wb+') as out_file:
    output = ""
    for book_title, book_clippings in separated_by_book.items():
        print(book_title)
        logseq_block = "\n\t- # [[Reference Notes]] for [[{book_title}]]\n\t\t- source::\n\t\t  url::\n\t\t- ## References:".format(book_title = book_title)
        logseq_sub_block_format = "\n\t\t\t- **Text**:\n\t\t\t  #+BEGIN_QUOTE\n\t\t\t  {text}\n\t\t\t  #+END_QUOTE\n\n\t\t\t  **Note**:\n\t\t\t  *{note}*\n\n\t\t\t  **Page**: {page}\n\t\t\t  **Location**: {location_start} - {location_end}\n\t\t\t  ---"
        for clipping in book_clippings:

            logseq_sub_block = logseq_sub_block_format.format(book_title, text = clipping.text.replace("\n", "\n\t\t\t  "), note = clipping.note, page = clipping.page, location_start = clipping.location_start, location_end = clipping.location_end)
            logseq_block += (logseq_sub_block)
        output += logseq_block
    out_file.write(output.encode())