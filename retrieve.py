class FileBasedRetrieval:
    def retrieve(self, query, user_id):
        # Stage 1: Category Selection (The Fix)
        # Instead of loading ALL content, we just list category NAMES and ask
        # the LLM which ones might contain the answer.
        all_categories = self.list_categories(user_id)
        relevant_categories = self.select_relevant_categories(query, all_categories)
        
        # Load only the relevant summaries
        summaries = {cat: self.load_category(user_id, cat) 
                     for cat in relevant_categories}
        
        # Stage 2: Sufficiency Check
        # Check if the high-level summaries answer the query
        if self.is_sufficient(query, summaries):
            return summaries
        
        # Stage 3: Hierarchical Search
        # If summaries are vague, generate a specific query to find atomic items
        # or raw resources.
        search_query = self.generate_search_query(query, summaries)
        
        # Search Level 1: Atomic Items (Extracted facts)
        items = self.search_items(user_id, search_query)
        if items:
            return items
            
        # Search Level 2: Raw Resources (Full text search fallback)
        resources = self.search_resources(user_id, search_query)
        return resources

    def select_relevant_categories(self, query, categories):
        """Filter to only the categories likely to hold the answer"""
        prompt = f"""Query: {query}
        Available Categories: {', '.join(categories)}
        
        Return a JSON list of the categories that are most relevant to this query."""
        return llm.invoke(prompt)

    def is_sufficient(self, query, summaries):
        prompt = f"""Query: {query}
        Summaries: {summaries}
        Can you answer the query comprehensively with just these summaries? YES/NO"""
        return 'YES' in llm.invoke(prompt)