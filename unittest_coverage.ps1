# a powershell script that runs 
coverage run -m unittest discover -s tests -p "test*.py" -v
coverage html

# if argument "donotopenhtml" is passed, do not open the htmlcov\index.html
if ($args[0] -ne "donotopenhtml") {
    start htmlcov\index.html
}
