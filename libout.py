from io import StringIO
import sys

old_stdout = sys.stdout
sys.stdout = str_stdout = StringIO()

print("before return ")
str_stdout.getvalue()
print("after get value return ")
str_stdout.getvalue()
sys.stdout = old_stdout
print("after back to normal ")
print(str_stdout.getvalue())
