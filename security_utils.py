import re

class SecurityFilter:
    def __init__(self):
        self.patterns = {
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'PHONE_TR': r'(?:\+90|0)?\s*5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}',
            'CREDIT_CARD': r'\b(?:\d[ -]*?){13,16}\b',
            'TCKN': r'\b[1-9]{1}[0-9]{10}\b',
            'IP_ADDRESS': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        }

    def sanitize_text(self, text: str) -> str:
        if not text:
            return ""
        
        sanitized_text = text
        
        for label, pattern in self.patterns.items():
            replacement = f"[CONFIDENTIAL_{label}]"
            sanitized_text = re.sub(pattern, replacement, sanitized_text)
            
        return sanitized_text

    def check_prompt_injection(self, text: str) -> bool:
        
        injection_patterns = [
            r"ignore previous instructions",
            r"system override",
            r"delete all logs",
            r"drop table",
            r"sistemi hackle",       
            r"tüm logları dök",      
            r"geçmişi sil",          
            r"şifreleri ver"         
        ]
        
        lower_text = text.lower()
        for pattern in injection_patterns:
            if re.search(pattern, lower_text):
                return True
        return False