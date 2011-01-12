
f = open("testfile2", 'w+')
text = f.read()
newtext = input()
byteswritten = f.write(newtext + '\n')
f.close()
