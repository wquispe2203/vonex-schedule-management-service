from html.parser import HTMLParser

class ActionPathParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag_repr = f"{tag}"
        if 'id' in attrs_dict:
            tag_repr += f"#{attrs_dict['id']}"
        if 'class' in attrs_dict:
            tag_repr += f".{attrs_dict['class'].replace(' ', '.')[:20]}"
            
        self.stack.append(tag_repr)
        
        if 'data-action' in attrs_dict:
            path = " > ".join(self.stack)
            print(f"ACTION FOUND AT: {path}")
            print(f"   Action value: {attrs_dict['data-action']}\n")
            
    def handle_endtag(self, tag):
        # Pop from stack safely
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i].split('#')[0].split('.')[0] == tag:
                self.stack = self.stack[:i]
                break

with open(r'd:\Desktop\MOD HOR\prototype\index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

parser = ActionPathParser()
parser.feed(html_content)
