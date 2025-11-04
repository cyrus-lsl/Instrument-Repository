import pandas as pd
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import difflib

class MeasurementInstrumentAgent:
    def __init__(self, excel_file_path, sheet_name=None, header_row=None):
        """Initialize the agent with the Excel data"""
        self.excel_file_path = excel_file_path
        self.sheet_name = sheet_name or 'Measurement Instruments'
        self.header_row = 0 if header_row is None else header_row

        if isinstance(self.excel_file_path, (str,)):
            if not os.path.exists(self.excel_file_path):
                raise FileNotFoundError(f"Excel file not found: {self.excel_file_path}")

        read_kwargs = {'sheet_name': self.sheet_name, 'header': self.header_row}
        self.df = pd.read_excel(excel_file_path, **read_kwargs)
        self.preprocess_data()
        self.setup_similarity_engine()
        
    def preprocess_data(self):
        """Clean and preprocess the data"""
        self.df = self.df.fillna('').astype(object)

        expected_cols = [
            'Measurement Instrument', 'Acronym', 'Outcome Domain',
            'Outcome Keywords', 'Purpose', 'Target Group(s)',
            'Cost', 'Permission to Use', 'Data Collection', 'Validated in Hong Kong',
            'No. of Questions / Statements', 'Scale', 'Scoring',
            'Download (Eng)', 'Download (Chi)', 'Citation',
            'Repository of Impact Measurement Instruments'
        ]

        for i in range(1, 4):
            expected_cols.append(f'Sample Question / Statement - {i}')

        lc_map = {c.lower(): c for c in self.df.columns}

        for col in expected_cols:
            if col not in self.df.columns:
                match = difflib.get_close_matches(col.lower(), lc_map.keys(), n=1, cutoff=0.6)
                if match:
                    matched_col = lc_map[match[0]]
                    self.df[col] = self.df[matched_col]
                else:
                    self.df[col] = ''

        self.df['combined_text'] = (
            self.df['Measurement Instrument'].astype(str) + ' ' +
            self.df['Acronym'].astype(str) + ' ' +
            self.df['Outcome Domain'].astype(str) + ' ' +
            self.df['Outcome Keywords'].astype(str) + ' ' +
            self.df['Purpose'].astype(str) + ' ' +
            self.df['Target Group(s)'].astype(str)
        )
        
    def setup_similarity_engine(self):
        """Set up TF-IDF for semantic search"""
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['combined_text'])
    
    def search_instruments(self, query, top_k=3):
        """
        Search for the most relevant instruments based on user query
        """
        if self.vectorizer is None or self.tfidf_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query])

        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:
                instrument_data = self.df.iloc[idx]
                results.append({
                    'instrument': instrument_data,
                    'similarity_score': similarities[idx],
                    'rank': len(results) + 1
                })
        
        return results
    
    def extract_scoring_info(self, instrument_data):
        """Extract and format scoring information"""
        scoring_info = {
            'scale': instrument_data.get('Scale', ''),
            'scoring': instrument_data.get('Scoring', ''),
            'interpretation': self.interpret_scoring(instrument_data.get('Scoring', ''))
        }
        return scoring_info
    
    def interpret_scoring(self, scoring_text):
        """Provide interpretation of scoring system"""
        scoring_text = str(scoring_text).lower()
        
        interpretations = []
        
        if 'higher' in scoring_text and 'better' in scoring_text:
            interpretations.append("Higher scores indicate better outcomes")
        elif 'lower' in scoring_text and 'better' in scoring_text:
            interpretations.append("Lower scores indicate better outcomes")
        
        if 'cut-off' in scoring_text or 'cutoff' in scoring_text:
            interpretations.append("Uses cut-off scores for interpretation")
            
        if 'age' in scoring_text and 'gender' in scoring_text:
            interpretations.append("Scoring varies by age and gender")
            
        return interpretations
    
    def generate_considerations(self, instrument_data):
        """Generate important considerations for the instrument"""
        considerations = []
        
        cost = instrument_data.get('Cost', '')
        if 'free' in str(cost).lower():
            considerations.append("✓ Free to use")
        else:
            considerations.append(f"Cost: {cost}")
        
        permission = instrument_data.get('Permission to Use', '')
        if 'not required' in str(permission).lower():
            considerations.append("✓ No permission required")
        else:
            considerations.append(f"Permission: {permission}")
        
        data_collection = instrument_data.get('Data Collection', '')
        if 'equipment' in str(data_collection).lower():
            considerations.append("⚠ Requires special equipment")
        if 'administered' in str(data_collection).lower():
            considerations.append("⚠ Requires trained administrator")
        
        validated = instrument_data.get('Validated in Hong Kong', '')
        if validated and str(validated).strip() and str(validated).lower() not in ['-', 'no']:
            considerations.append("✓ Validated in Hong Kong context")
        else:
            considerations.append("⚠ Not specifically validated for Hong Kong")
        
        return considerations
    
    def generate_advantages_disadvantages(self, instrument_data):
        """Generate advantages and disadvantages based on instrument characteristics"""
        advantages = []
        disadvantages = []
        
        num_questions = instrument_data.get('No. of Questions / Statements', '')
        num_q_int = None
        if isinstance(num_questions, (int, float)):
            num_q_int = int(num_questions)
        else:
            import re as _re
            m = _re.search(r"(\d+)", str(num_questions))
            if m:
                num_q_int = int(m.group(1))

        if num_q_int == 1:
            advantages.append("Quick to administer (single item)")
        elif num_q_int is not None and num_q_int > 10:
            disadvantages.append("Time-consuming due to many items")
        else:
            advantages.append("Reasonable administration time")
        
        data_collection = str(instrument_data.get('Data Collection', '')).lower()
        if 'self-administered' in data_collection:
            advantages.append("Can be self-administered")
        if 'equipment' in data_collection:
            disadvantages.append("Requires specific equipment")
        if 'trained' in data_collection:
            disadvantages.append("Requires trained administrator")
        
        has_sample_questions = any(
            instrument_data.get(f'Sample Question / Statement - {i}', '') not in ['', '-']
            for i in range(1, 4)
        )
        if has_sample_questions:
            advantages.append("Well-documented with sample items")
        
        return advantages, disadvantages
    
    def process_query(self, user_query):
        """
        Main method to process user query and return recommendations
        """
        results = self.search_instruments(user_query)
        
        if not results:
            return "No suitable instruments found for your query. Please try different keywords."
        
        response = {
            'query': user_query,
            'recommendations': []
        }
        
        for result in results:
            instrument_data = result['instrument']
            
            recommendation = {
                'name': instrument_data['Measurement Instrument'],
                'acronym': instrument_data['Acronym'],
                'purpose': instrument_data['Purpose'],
                'target_group': instrument_data['Target Group(s)'],
                'domain': instrument_data['Outcome Domain'],
                'similarity_score': round(result['similarity_score'], 3),
                'scoring_info': self.extract_scoring_info(instrument_data),
                'considerations': self.generate_considerations(instrument_data),
                'advantages': [],
                'disadvantages': [],
                'num_questions': instrument_data.get('No. of Questions / Statements', ''),
                'resources': {
                    'english_download': instrument_data.get('Download (Eng)', ''),
                    'chinese_download': instrument_data.get('Download (Chi)', ''),
                    'citation': instrument_data.get('Citation', '')
                }
            }
            
            advantages, disadvantages = self.generate_advantages_disadvantages(instrument_data)
            recommendation['advantages'] = advantages
            recommendation['disadvantages'] = disadvantages
            
            response['recommendations'].append(recommendation)
        return response
    
    
    def format_response(self, processed_results):
        """Format the response in a user-friendly way"""
        if isinstance(processed_results, str):
            return processed_results
        
        response = f"🔍 **Recommendations for: \"{processed_results['query']}\"**\n\n"
        
        for i, rec in enumerate(processed_results['recommendations'], 1):
            response += f"**{i}. {rec['name']} ({rec['acronym']})**\n"
            response += f"   • **Relevance Score**: {rec['similarity_score']}/1.0\n"
            response += f"   • **Purpose**: {rec['purpose']}\n"
            response += f"   • **Target Group**: {rec['target_group']}\n"
            response += f"   • **Domain**: {rec['domain']}\n"
            response += f"   • **Items**: {rec['num_questions']} questions\n\n"
            
            response += f"   **Scoring Information**:\n"
            response += f"   - Scale: {rec['scoring_info']['scale']}\n"
            response += f"   - Scoring: {rec['scoring_info']['scoring']}\n"
            if rec['scoring_info']['interpretation']:
                for interpret in rec['scoring_info']['interpretation']:
                    response += f"   - {interpret}\n"
            
            response += f"\n   **Advantages**:\n"
            for adv in rec['advantages']:
                response += f"   ✓ {adv}\n"
                
            response += f"\n   **Disadvantages**:\n"
            for disadv in rec['disadvantages']:
                response += f"   ⚠ {disadv}\n"
            
            response += f"\n   **Important Notes**:\n"
            for consideration in rec['considerations']:
                response += f"   • {consideration}\n"
            
            response += "\n" + "-"*50 + "\n\n"
        return response

    def filter_by_criteria(self, criteria):
        """
        Filter instruments by specific criteria
        criteria example: {
            'domain': 'Health',
            'cost': 'Free',
            'target_group': 'elderly',
            'validated_hk': True
        }
        """
        filtered_df = self.df.copy()
        
        if criteria.get('domain'):
            filtered_df = filtered_df[filtered_df['Outcome Domain'].str.contains(
                criteria['domain'], case=False, na=False)]
        
        if criteria.get('cost') == 'Free':
            filtered_df = filtered_df[filtered_df['Cost'].str.contains(
                'free', case=False, na=False)]
        
        if criteria.get('target_group'):
            filtered_df = filtered_df[filtered_df['Target Group(s)'].str.contains(
                criteria['target_group'], case=False, na=False)]
        
        return filtered_df
    
    def get_instrument_details(self, instrument_name):
        """Get detailed information about a specific instrument"""
        instrument = self.df[
            self.df['Measurement Instrument'].str.contains(
                instrument_name, case=False, na=False)
        ]
        
        if not instrument.empty:
            return instrument.iloc[0].to_dict()
        return None

    def interactive_mode(self):
        """Run the agent in interactive mode"""
        print("🤖 Measurement Instrument Recommendation Agent")
        print("Type 'quit' to exit\n")
        
        while True:
            user_input = input("What type of measurement instrument are you looking for? ")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            results = self.process_query(user_input)
            response = self.format_response(results)
            print("\n" + response)