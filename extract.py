import subprocess

text = subprocess.check_output(['git', 'show', 'HEAD^^:app.js']).decode('utf-8')
s = text.find('const btnPedido')
e = text.find('const posModal', s)

with open('deleted.js', 'w', encoding='utf-8') as f:
    f.write(text[s:e])
