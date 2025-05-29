import numpy as np
import argparse
import sys
from astropy.table import Table
from fuzzywuzzy import fuzz, process

def parse_author_list(filename):
    """Parse a file containing author names (first initial and last name, one per line)"""
    authors = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    authors.append(line)
    except FileNotFoundError:
        print(f"Error: Could not find file {filename}")
        sys.exit(1)
    return authors

def find_author_name_in_table(full_name, table):
    """Find the corresponding Authorname in the table for a given full name"""
    # Split the full name into parts
    name_parts = full_name.strip().split()
    if len(name_parts) < 2:
        return None
    
    # Try different combinations of first name and last name
    # For "Johannes Ulf Lange", try:
    # 1. first="Johannes", last="Ulf Lange"
    # 2. first="Johannes Ulf", last="Lange"
    
    for i in range(1, len(name_parts)):
        first_name = ' '.join(name_parts[:i]).strip()
        last_name = ' '.join(name_parts[i:]).strip()
        
        # Look for matches in the table
        for row in table:
            # Check if firstname and lastname match (handle extra whitespace and commas)
            table_first = str(row['Firstname']).strip()
            table_last = str(row['Lastname']).strip().rstrip(',')  # Remove trailing comma and whitespace
            
            if (table_first.lower() == first_name.lower() and 
                table_last.lower() == last_name.lower()):
                return row['Authorname']
    
    return None

def find_closest_author_match(target_name, table, threshold=70):
    """Find the closest author matches using fuzzy string matching"""
    # Create list of full names from the table for comparison
    full_names = []
    for row in table:
        first = str(row['Firstname']).strip()
        last = str(row['Lastname']).strip().rstrip(',')
        full_name = f"{first} {last}"
        full_names.append((full_name, row['Authorname']))
    
    # Find the best matches (top 3)
    best_matches = process.extract(target_name, [name for name, _ in full_names], limit=3)
    
    # Filter matches above threshold and create result list
    valid_matches = []
    for match_name, confidence in best_matches:
        if confidence >= threshold:
            # Find the corresponding Authorname
            for full_name, author_name in full_names:
                if full_name == match_name:
                    valid_matches.append((author_name, confidence, full_name))
                    break
    
    return valid_matches

def ask_user_confirmation(target_name, matches):
    """Ask user to choose from multiple suggested matches"""
    print(f"\nInfrastructure author '{target_name}' not found exactly.")
    print("Possible matches:")
    
    for i, (author_name, confidence, full_name) in enumerate(matches, 1):
        print(f"  {i}. {full_name} (confidence: {confidence}%)")
    
    print("  0. None of the above (skip this author)")
    
    while True:
        try:
            response = input(f"Select match (0-{len(matches)}): ").strip()
            choice = int(response)
            
            if choice == 0:
                return None  # No match selected
            elif 1 <= choice <= len(matches):
                return matches[choice - 1]  # Return the selected match tuple
            else:
                print(f"Please enter a number between 0 and {len(matches)}.")
        except ValueError:
            print("Please enter a valid number.")

def generate_numbered_affiliation_output(table, authors_file, affiliations_file, include_orcid_links=True):
    """Generate alternative output format with numbered affiliations"""
    # Build mapping of unique affiliations to numbers
    affiliation_to_number = {}
    next_number = 1
    
    # First pass: identify all unique affiliations in order of first appearance
    for row in table:
        affls = row['Affiliations']
        for affl in affls:
            if affl != '' and affl not in affiliation_to_number:
                affiliation_to_number[affl] = next_number
                next_number += 1
    
    # Write authors file
    with open(authors_file, "w") as fstream:
        for row in table:
            name = row['Authorname']
            orcid = row['ORCID']
            affls = row['Affiliations']
            
            # Build author line with optional ORCID link
            author_line = ""
            if include_orcid_links and orcid != '':
                author_line += r"\orcidlink{" + orcid + "}"
            
            # Get affiliation numbers for this author
            affl_numbers = []
            for affl in affls:
                if affl != '':
                    affl_numbers.append(str(affiliation_to_number[affl]))
            
            if affl_numbers:
                numbers_str = ','.join(affl_numbers)
                author_line += f"{name},$^{{{numbers_str}}}$\n"
            else:
                author_line += f"{name}\n"
            
            fstream.write(author_line)
    
    # Write affiliations file
    with open(affiliations_file, "w") as fstream:
        # Sort affiliations by their assigned numbers
        sorted_affiliations = sorted(affiliation_to_number.items(), key=lambda x: x[1])
        for affiliation, number in sorted_affiliations:
            fstream.write(f"$^{{{number}}}$ {affiliation} \\\\\n")

def main():
    parser = argparse.ArgumentParser(description='Generate author list for academic papers')
    parser.add_argument('input_csv', help='Input CSV file with author information')
    parser.add_argument('output_tex', help='Output TeX file for author list')
    parser.add_argument('output_csv', help='Output CSV file for AAS journal submission')
    parser.add_argument('--first-tier', required=True, help='File containing first-tier authors (one per line)')
    parser.add_argument('--infrastructure', required=True, help='File containing infrastructure authors (one per line)')
    parser.add_argument('--users-csv', default='Users.csv', help='CSV file with user emails (default: Users.csv)')
    parser.add_argument('--alt-authors-tex', help='Alternative output: authors with numbered affiliations')
    parser.add_argument('--alt-affiliations-tex', help='Alternative output: numbered affiliations list')
    parser.add_argument('--no-fuzzy-matching', action='store_true', help='Disable interactive fuzzy matching for infrastructure authors')
    parser.add_argument('--no-orcid-links', action='store_true', help='Disable ORCID links in author output (default: enabled)')
    
    args = parser.parse_args()
    
    # Check that both alt files are specified together or neither
    if bool(args.alt_authors_tex) != bool(args.alt_affiliations_tex):
        print("Error: Both --alt-authors-tex and --alt-affiliations-tex must be specified together")
        sys.exit(1)
    
    # Parse author lists
    first_tier_authors = parse_author_list(args.first_tier)
    infrastructure_authors = parse_author_list(args.infrastructure)
    
    print(f"First-tier authors: {first_tier_authors}")
    print(f"Infrastructure authors: {infrastructure_authors}")

    # Read the main author table
    try:
        table = Table.read(args.input_csv)
    except FileNotFoundError:
        print(f"Error: Could not find input file {args.input_csv}")
        sys.exit(1)
    

    # Merge entries of the same person and different affiliations.
    table['Affiliations'] = np.zeros(
        (len(table), np.amax(
            np.unique(table['Authorname'], return_counts=True)[1])), dtype='U1000')
    table['Country'] = np.zeros(len(table), dtype='S100')
    for name in np.unique(table['Authorname']):
        use = table['Authorname'] == name
        table['Affiliations'][use, :np.sum(use)] = table['Affiliation'][use]

    table.remove_column('Affiliation')
    table = table[np.unique(table['Authorname'], return_index=True)[1]]

    # Add emails.
    table['Email'] = np.zeros(len(table), dtype='S100')
    try:
        database = Table.read(args.users_csv)
        for row in table:
            name = f"{row['Lastname']},&nbsp;{row['Firstname']}"
            use = database['Name'] == name
            if np.sum(use) != 1:
                print(f"Can't find email for {row['Firstname']} {row['Lastname']}.")
            else:
                row['Email'] = database['Email'][use][0]
    except FileNotFoundError:
        print(f"Warning: Could not find {args.users_csv}, proceeding without emails")

    # New author ordering logic
    table['Order'] = np.full(len(table), 99999)  # Default very high order
    current_order = 1
    
    # 1. First-tier authors in specified order
    for author_name in first_tier_authors:
        # Find the corresponding Authorname in the table
        table_author_name = find_author_name_in_table(author_name, table)
        if table_author_name is None:
            print(f"Error: First-tier author '{author_name}' not found in author list")
            sys.exit(1)
        
        matching_rows = table['Authorname'] == table_author_name
        if not np.any(matching_rows):
            print(f"Error: First-tier author '{author_name}' ('{table_author_name}') not found in author list")
            sys.exit(1)
        table['Order'][matching_rows] = current_order
        current_order += 1
    
    # 2. Infrastructure authors in alphabetical order by last name
    # Exclude authors who are already in first-tier
    first_tier_author_names = set()
    first_tier_original_names = set(first_tier_authors)  # Keep track of original names too
    
    for author_name in first_tier_authors:
        table_author_name = find_author_name_in_table(author_name, table)
        if table_author_name is not None:
            first_tier_author_names.add(table_author_name)
    
    infrastructure_found = []
    unmatched_infrastructure = []
    
    for author_name in infrastructure_authors:
        # Skip if this author is already in the first-tier list
        if author_name in first_tier_original_names:
            continue
            
        # First try exact matching
        table_author_name = find_author_name_in_table(author_name, table)
        
        if table_author_name is not None and table_author_name not in first_tier_author_names:
            matching_rows = table['Authorname'] == table_author_name
            if np.any(matching_rows):
                # Get the row to access the Lastname field
                row_index = np.where(matching_rows)[0][0]
                infrastructure_found.append((table_author_name, table['Lastname'][row_index]))
        else:
            # If not found exactly, try fuzzy matching
            matched = False
            if not args.no_fuzzy_matching:
                closest_matches = find_closest_author_match(author_name, table)
                
                if closest_matches:
                    # Filter out matches that are already first-tier authors
                    available_matches = []
                    for match_author_name, confidence, full_name in closest_matches:
                        if match_author_name not in first_tier_author_names:
                            available_matches.append((match_author_name, confidence, full_name))
                    
                    if available_matches:
                        # Ask user to choose from available matches
                        selected_match = ask_user_confirmation(author_name, available_matches)
                        
                        if selected_match is not None:
                            selected_author_name, confidence, full_name = selected_match
                            matching_rows = table['Authorname'] == selected_author_name
                            if np.any(matching_rows):
                                row_index = np.where(matching_rows)[0][0]
                                infrastructure_found.append((selected_author_name, table['Lastname'][row_index]))
                                print(f"Added '{full_name}' as infrastructure author.")
                                matched = True
                        else:
                            print(f"Skipping '{author_name}' - no match selected.")
                    else:
                        print(f"Warning: All matches for '{author_name}' are already first-tier authors")
                else:
                    print(f"Warning: No good match found for infrastructure author '{author_name}'")
            else:
                print(f"Warning: Infrastructure author '{author_name}' not found exactly (fuzzy matching disabled)")
            
            # If no match was found or confirmed, add to unmatched list
            if not matched:
                unmatched_infrastructure.append(author_name)
    
    # Sort infrastructure authors alphabetically by last name
    infrastructure_sorted = sorted(infrastructure_found, key=lambda x: x[1].upper())
    
    for table_author_name, _ in infrastructure_sorted:
        matching_rows = table['Authorname'] == table_author_name
        if np.any(matching_rows):
            table['Order'][matching_rows] = current_order
            current_order += 1
    
    # 3. Remaining authors in alphabetical order by last name
    remaining_authors = []
    for row in table:
        if row['Order'] == 99999:  # Not yet assigned
            remaining_authors.append((row['Authorname'], row['Lastname']))
    
    # Sort remaining authors by last name
    remaining_sorted = sorted(remaining_authors, key=lambda x: x[1].upper())
    
    for author_name, _ in remaining_sorted:
        matching_rows = table['Authorname'] == author_name
        table['Order'][matching_rows] = current_order
        current_order += 1

    # Sort the table by the new order
    table.sort('Order')
    table['Order'] = np.arange(len(table)) + 1

    # Write the author list into a TeX file useable with AASTeX.
    with open(args.output_tex, "w") as fstream:
        for row in table:
            name = row['Authorname']
            orcid = row['ORCID']
            email = row['Email']
            affls = row['Affiliations']
            
            # Build author line with optional ORCID link
            author_line = ""
            if not args.no_orcid_links and orcid != '':
                author_line += r"\orcidlink{" + orcid + "}"
            
            if orcid != '':
                author_line += r"\author[" + orcid + "]{" + name + "}\n"
            else:
                author_line += r"\author{" + name + "}\n"
            
            fstream.write(author_line)
            
            for affl in affls:
                if affl != '':
                    fstream.write(r"\affiliation{" + affl + "}\n")
            fstream.write("\n")

    # Write the author list into a table that can be copy-pasted into the AAS
    # xls template such that we don't need to manually enter that info in the
    # journal submission page.
    output_table = table[['Order', 'Firstname', 'Lastname', 'Email']]
    output_table.write(args.output_csv, overwrite=True)
    
    print(f"Successfully generated {args.output_tex} and {args.output_csv}")
    print(f"Total authors: {len(table)}")

    if args.alt_authors_tex and args.alt_affiliations_tex:
        generate_numbered_affiliation_output(table, args.alt_authors_tex, args.alt_affiliations_tex, 
                                            include_orcid_links=not args.no_orcid_links)
        print(f"Also generated alternative format: {args.alt_authors_tex} and {args.alt_affiliations_tex}")
    
    # Report unmatched infrastructure authors
    if unmatched_infrastructure:
        print(f"\nInfrastructure authors not found in author list ({len(unmatched_infrastructure)}):")
        for author in unmatched_infrastructure:
            print(f"  - {author}")
    else:
        print("\nAll infrastructure authors were successfully matched.")

if __name__ == "__main__":
    main()
