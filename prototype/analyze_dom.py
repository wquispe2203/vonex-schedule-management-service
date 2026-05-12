import re
from html.parser import HTMLParser

class ActionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.elements_with_action = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        has_action = 'data-action' in attrs_dict
        el_id = attrs_dict.get('id', '')
        action = attrs_dict.get('data-action', '')
        
        self.stack.append({
            'tag': tag,
            'id': el_id,
            'action': action
        })
        
        if has_action:
            # Find ancestors
            ancestors = []
            for parent in self.stack[:-1]:
                if parent['action']:
                    ancestors.append(f"{parent['tag']}#{parent['id']}({parent['action']})")
            
            self.elements_with_action.append({
                'tag': tag,
                'id': el_id,
                'action': action,
                'ancestors_with_action': ancestors
            })

    def handle_endtag(self, tag):
        if self.stack:
            self.stack.pop()

with open(r'd:\Desktop\MOD HOR\prototype\index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

parser = ActionParser()
parser.feed(html_content)

print("=== ELEMENTS WITH DATA-ACTION AND NESTED ACTIONS ===")
for item in parser.elements_with_action:
    if item['ancestors_with_action']:
        print(f"WARNING: Nested data-action! <{item['tag']} id='{item['id']}' data-action='{item['action']}'> is nested inside: {item['ancestors_with_action']}")
    else:
        print(f"<{item['tag']} id='{item['id']}' data-action='{item['action']}'>")

print("\n=== SEARCHING FOR INPUTS INSIDE DATA-ACTION ELEMENTS ===")
# Re-parse to find inputs inside action elements
class InputInActionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.action_stack = []
        self.violations = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        action = attrs_dict.get('data-action', '')
        
        if action:
            self.action_stack.append({
                'tag': tag,
                'id': attrs_dict.get('id', ''),
                'action': action
            })
        else:
            # Still push dummy entry to maintain stack depth for this element (we pop in endtag)
            # Wait, to properly track nesting, we need full element stack, not just actions
            pass

    # Let's rewrite this tracker properly using a full stack

class InputInActionParserV2(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.violations = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        action = attrs_dict.get('data-action', '')
        
        el_info = {
            'tag': tag,
            'id': attrs_dict.get('id', ''),
            'action': action
        }
        
        # Check if this tag is an input/select/textarea
        if tag in ['input', 'select', 'textarea']:
            # Find if any ancestor has a data-action
            for ancestor in reversed(self.stack):
                if ancestor['action']:
                    self.violations.append({
                        'input_tag': tag,
                        'input_id': el_info['id'],
                        'input_action': action,
                        'ancestor_tag': ancestor['tag'],
                        'ancestor_id': ancestor['id'],
                        'ancestor_action': ancestor['action']
                    })
                    break
        
        self.stack.append(el_info)

    def handle_endtag(self, tag):
        # Pop until we match the tag (basic HTML robust pop)
        found = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]['tag'] == tag:
                self.stack = self.stack[:i]
                found = True
                break

parser2 = InputInActionParserV2()
parser2.feed(html_content)

if parser2.violations:
    print("CRITICAL VIOLATIONS FOUND: Input elements nested inside data-action containers!")
    for v in parser2.violations:
        print(f"- <{v['input_tag']} id='{v['input_id']}'> is nested inside <{v['ancestor_tag']} id='{v['ancestor_id']}' data-action='{v['ancestor_action']}'>")
else:
    print("NO inputs nested inside data-action containers. Bubbling should be safe.")
