import nltk
import webbrowser
import re

# Download NLTK data if you haven't already
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except nltk.downloader.DownloadError:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')

def process_user_query(user_input):
    """
    Processes the user's input to extract a question and perform a search
    on a specified website or Google by default.
    """
    # Define search providers and their base URLs
    # %s will be replaced by the search query
    search_providers = {
        "google": "https://www.google.com/search?q=%s",
        "youtube": "https://www.youtube.com/results?search_query=%s",
        "x": "https://twitter.com/search?q=%s", # X (formerly Twitter)
        "twitter": "https://twitter.com/search?q=%s",
        "linkedin": "https://www.linkedin.com/search/results/all/?keywords=%s",
        # Add more search providers here
        # "wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search=%s",
    }

    # Keywords for general search command, excluding specific website names for now
    general_search_phrases = [
        "search for", "look for", "find", "see", "lookup", "check"
    ]

    normalized_input = user_input.lower()
    
    # Default to Google if no specific website is mentioned
    target_website = "google"
    question = ""
    found_search_command = False

    # 1. Identify the target website first
    for site_name in search_providers.keys():
        # Look for phrases like "search on youtube", "see in x", "linkedin search for"
        if f" on {site_name}" in normalized_input or \
           f" in {site_name}" in normalized_input or \
           f" {site_name} search for" in normalized_input or \
           f" search {site_name} for" in normalized_input:
            target_website = site_name
            found_search_command = True
            break
    
    # 2. Extract the question after identifying the target website
    # Create a regex pattern to remove all identified search command phrases and website names
    # This pattern needs to be carefully constructed to avoid removing parts of the question
    
    # Combine general search phrases and specific site-related phrases
    all_removal_patterns = []
    for phrase in general_search_phrases:
        all_removal_patterns.append(re.escape(phrase))
    
    for site_name in search_providers.keys():
        all_removal_patterns.append(re.escape(f" on {site_name}"))
        all_removal_patterns.append(re.escape(f" in {site_name}"))
        all_removal_patterns.append(re.escape(f" {site_name} search for"))
        all_removal_patterns.append(re.escape(f" search {site_name} for"))
        # Add the site name itself, in case it's used directly like "youtube what is..."
        all_removal_patterns.append(re.escape(site_name))


    # Make the regex pattern
    removal_regex = r'\b(?:' + '|'.join(all_removal_patterns) + r')\b'
    
    # Remove the search command parts
    temp_question = re.sub(removal_regex, '', normalized_input).strip()

    # Further clean up common conversational fillers or leading question words if they are now at the start
    temp_question = re.sub(r'^(?:please|can you|could you|what is|how to|where is|when did|who is)\s*', '', temp_question, flags=re.IGNORECASE).strip()
    
    # Remove any remaining leading/trailing punctuation or "that"
    question = re.sub(r'^\W+|\W+$', '', temp_question).strip()
    
    # Handle cases where the whole input might just be the question without a clear command
    if not found_search_command and any(phrase in normalized_input for phrase in general_search_phrases):
        print("I found a general search command but no specific website. Defaulting to Google.")
        # Try to extract the question by just removing general phrases
        for phrase in general_search_phrases:
            if phrase in normalized_input:
                parts = normalized_input.split(phrase, 1) # Split only once
                if len(parts) > 1:
                    question = parts[1].strip()
                    break
        if not question and normalized_input: # If no specific phrase worked, assume whole input is question
             question = normalized_input
             
        question = re.sub(r'^\W+|\W+$', '', question).strip()
        question = re.sub(r'^(?:please|can you|could you|what is|how to|where is|when did|who is)\s*', '', question, flags=re.IGNORECASE).strip()
        
    elif not found_search_command and not question: # If no command found at all, treat whole input as question
        print("No specific search command or website found. Treating the entire input as the question for Google.")
        question = user_input.strip()

    if question:
        # Encode the query for URL
        search_query_encoded = re.sub(r'\s+', '%20', question) # Replace spaces with %20 for URL encoding
        search_query_encoded = re.sub(r'[^\w\s-]', '', search_query_encoded) # Remove non-alphanumeric except space and hyphen
        search_query_encoded = search_query_encoded.replace(" ", "%20") # Final encoding for spaces

        target_url = search_providers[target_website] % search_query_encoded

        print(f"\nSearching '{question}' on {target_website.capitalize()}...")
        print(f"Opening URL: {target_url}")
        webbrowser.open(target_url)
    else:
        print("Could not extract a valid question from your input. Please try again.")
        print(f"Original input: {user_input}")

if __name__ == "__main__":
    print("Welcome! I can help you search various websites.")
    print("Try asking something like:")
    print("  - 'What is the capital of France search in google?'")
    print("  - 'Search on youtube how to bake a cake'")
    print("  - 'See in x latest tech news'")
    print("  - 'Find on linkedin job openings in software development'")
    print("  - 'How to install python on windows'") # This will default to Google

    user_input = input("\nEnter your query: ")
    process_user_query(user_input)