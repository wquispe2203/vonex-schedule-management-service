from html.parser import HTMLParser

class ActionInputIntegrityParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.element_stack = []
        self.action_elements = []
        self.inputs_inside_action = []
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        action = attrs_dict.get('data-action', '')
        el_id = attrs_dict.get('id', '')
        
        el_info = {
            'tag': tag,
            'id': el_id,
            'action': action
        }
        
        # Record all action elements
        if action:
            self.action_elements.append(el_info)
            
        # Check if this is an input/select/textarea nested inside an element WITH action
        if tag in ['input', 'select', 'textarea', 'button']:
            for parent in reversed(self.element_stack):
                if parent['action']:
                    self.inputs_inside_action.append({
                        'element': f"<{tag} id='{el_id}'>",
                        'parent': f"<{parent['tag']} id='{parent['id']}' data-action='{parent['action']}'>"
                    })
                    break # Found closest action parent
                    
        self.element_stack.append(el_info)
        
    def handle_endtag(self, tag):
        # Robust stack popping to handle unclosed tags if any
        for i in range(len(self.element_stack) - 1, -1, -1):
            if self.element_stack[i]['tag'] == tag:
                self.element_stack = self.element_stack[:i]
                break

with open(r'd:\Desktop\MOD HOR\prototype\index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

parser = ActionInputIntegrityParser()
parser.feed(html_content)

print("=== ALL DATA-ACTION ELEMENTS IN INDEX.HTML ===")
for item in parser.action_elements:
    print(f"<{item['tag']} id='{item['id']}' data-action='{item['action']}'>")

print("\n=== INPUTS/SELECTS/BUTTONS NESTED INSIDE A DATA-ACTION PARENT ===")
if parser.inputs_inside_action:
    for vi in parser.inputs_inside_action:
        print(f"- {vi['element']} is inside {vi['parent']}")
else:
    print("None found! All inputs and buttons are topologically isolated from parent data-actions.")
