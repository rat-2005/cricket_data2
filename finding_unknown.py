import json

def filter_and_save_links():
    # 1. Extract links from the text file
    try:
        with open('unique_urls_list.txt', 'r') as txt_file:
            txt_urls = set(line.strip() for line in txt_file if line.strip())
    except FileNotFoundError:
        print("Error: 'unique_urls_list.txt' not found.")
        return

    # 2. Extract links directly from the JSON list
    try:
        with open('events.json', 'r') as json_file:
            # json.load() instantly converts the JSON array into a Python list
            json_list = json.load(json_file)
            json_urls = set(json_list)
    except FileNotFoundError:
        print("Error: 'events.json' not found.")
        return
    except json.JSONDecodeError:
        print("Error: 'events.json' is not properly formatted.")
        return

    # 3. Keep only the links that are NOT in both files
    unmatched_urls = list(txt_urls.symmetric_difference(json_urls))

    # 4. Save the result as a Python list in a new .py file
    output_filename = 'filtered_links_list.py'
    with open(output_filename, 'w') as out_file:
        out_file.write("filtered_urls = [\n")
        for url in unmatched_urls:
            out_file.write(f"    '{url}',\n")
        out_file.write("]\n")

    # Output the final count
    print(f"Success! {len(unmatched_urls)} non-overlapping links found.")
    print(f"They have been saved as a Python list inside '{output_filename}'.")

# Run the function
filter_and_save_links()