from datetime import datetime
import sys
import os
import re



highlight_format = """ 
- type:: [[highlight]]
  book:: [[{}]]
  author:: {}
  date:: [[{}]]
  time:: {}
  page:: {}
  location-start:: {}
  location-end:: {}
  tags::
    - #+BEGIN_QUOTE
      {}
      #+END_QUOTE
    - {}

"""



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
                    # print(line)
                    # print(data_parts[1].split("location "))
                    location_data = data_parts[1].split("location ")[1].split("-")
                    location_start = int(location_data[0])
                    location_end = int(location_data[1])
                else:
                    is_note = True
                    # print(line)
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

def sanitize_filename(filename):
    """Sanitizes a filename by replacing invalid characters with underscores.

    Args:
        filename: The filename to sanitize.

    Returns:
        The sanitized filename.
    """
    pattern = r"[^\w\-_\. ]{1,}"  # Match one or more characters that are not alphanumeric, underscore, hyphen, dot, or space
    replacement = "_"
    return re.sub(pattern, replacement, filename)

# MAIN

clippings_file_name, clippings_file_extension = os.path.splitext("My Clippings.txt") 

clippings = parse_highlight_file(clippings_file_name + clippings_file_extension)
separated_by_book = separate_clippings_by_book(clippings)
output_directory = "output"
sub_block_new_line = "\n\t\t  "

for book_title, book_clippings in separated_by_book.items():
    sanitzied_book_title = sanitize_filename(book_title)
    directory = os.path.join(output_directory, sanitzied_book_title)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            # print("Directory created successfully!")
        except OSError as error:
            print(f"Error creating directory: {error}")
            continue
    new_file_path = os.path.join(directory, sanitzied_book_title)
    with open(new_file_path + ".md", 'wb+') as out_file:
        output = ""
        for clipping in book_clippings:
            authors = [clipping.author]
            if '&' in clipping.author:
                authors = clipping.author.split("&")    
            elif ';' in clipping.author:
                authors = clipping.author.split(";")    
            authors = ['[[' + element.strip() + ']]' for element in authors]
            authors_string = ", ".join(authors)
            hightlight_logseq_block = highlight_format.format(book_title, authors_string, clipping.date.strftime("%d.%m.%Y"), clipping.date.strftime("%H:%M:%S"), clipping.page, clipping.location_start, clipping.location_end, clipping.text.replace("\n", "\n\t  "), clipping.note) 
        output += hightlight_logseq_block
        out_file.write(output.encode())