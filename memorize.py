import json

class FileBasedMemory:
    def memorize(self, conversation_text, user_id):
        # Stage 1: Resource Ingestion (The Source of Truth)
        # Always save the raw input first. This allows for traceability.
        resource_id = self.save_resource(user_id, conversation_text)
        
        # Stage 2: Extraction
        # Extract atomic facts from the conversation.
        items = self.extract_items(conversation_text)
        
        # Stage 3: Batching (The Fix)
        # Group items by category to avoid opening/writing files multiple times.
        # Structure: { "work_life": ["User hates Java", "User loves Python"], ... }
        updates_by_category = {}
        for item in items:
            cat = self.classify_item(item)
            if cat not in updates_by_category:
                updates_by_category[cat] = []
            updates_by_category[cat].append(item['content'])
            
            # Link item to the specific resource for traceability
            self.save_item(user_id, category=cat, item=item, source_resource_id=resource_id)

        # Stage 4: Evolve Summaries (One Write Per Category)
        for category, new_memories in updates_by_category.items():
            existing_summary = self.load_category(user_id, category)
            
            # We pass the LIST of new memories, not just one
            updated_summary = self.evolve_summary(
                existing=existing_summary,
                new_memories=new_memories
            )
            
            self.save_category(user_id, category, updated_summary)

    def extract_items(self, text):
        """Use LLM to extract atomic facts"""
        prompt = f"""Extract discrete facts from this conversation.
        Focus on preferences, behaviors, and important details.
        Conversation: {text}
        Return as JSON list of items."""
        return llm.invoke(prompt)

    def evolve_summary(self, existing, new_memories):
        """
        Update category summary with a BATCH of new information.
        """
        # Convert list to bullet points for the prompt
        memory_list_text = "\n".join([f"- {m}" for m in new_memories])
        
        prompt = f"""You are a Memory Synchronization Specialist.
        
        Topic Scope: User Profile
        
        ## Original Profile
        {existing if existing else "No existing profile."}
        
        ## New Memory Items to Integrate
        {memory_list_text}
        
        # Task
        1. Update: If new items conflict with the Original Profile, overwrite the old facts.
        2. Add: If items are new, append them logically.
        3. Output: Return ONLY the updated markdown profile."""
        
        return llm.invoke(prompt)

    # Helper stubs
    def save_resource(self, user_id, text): pass
    def save_item(self, user_id, category, item, source_resource_id): pass
    def save_category(self, user_id, category, content): pass
    def load_category(self, user_id, category): return ""
    def classify_item(self, item): return "general"