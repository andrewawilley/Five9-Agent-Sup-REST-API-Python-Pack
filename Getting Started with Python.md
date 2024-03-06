If you have never used Python before, this brief guide will help you understand some of the basics.  This guide is not comprehensive, but it should give you enough information to get started and to understand some of the terminology and concepts you will encounter as you learn more about these tools.  

* Install [Python](https://www.Python.org/downloads/windows/)
    * Download the 64-bit version of Python 3.12.  The majority of defaults are fine.  Make sure to check the box to add Python to your PATH and to increase the PATH character limit.  This will make it easier to run Python from the command line.


# The Python "Environment"
Python has a "standard library" of modules that are included with the language.  These standard modules are always available to you.  When writing scripts, you can use these modules to perform a wide variety of tasks such as reading and writing files, working with dates and times, and interacting with the operating system.

In addition to the standard library, there are thousands of third-party modules that you can install to extend the functionality of Python.  There are libraries that can be used for data analysis, web development, machine learning, and much more.  

The version of Python you have installed, along with any additional libraries you have installed, is referred to as your "Python environment".  When writing a script or running a Python shell session, you can "import" modules from your environment to use their functionality.  For example, you might import the `os` module to work with files and directories, or the `requests` module to make HTTP requests.

Many of these libraries depend on having other Python libraries installed, and may even have a specific version of the library that they depend on.  This can make managing your Python environment a bit tricky.

To help make this easier and less prone to error, it is common to use a tool called a "virtual environment" to manage your Python environment.  A virtual environment is a self-contained directory that contains a Python installation for a particular version of Python, plus a number of additional packages.  This allows you to have multiple virtual environments on your computer, each with different versions of Python and different sets of packages (and even different versions of the same package).

## Creating a Virtual Environment
You can use the `venv` module that comes with Python to create a virtual environment.  Open a command prompt and navigate to the directory where you want to create the virtual environment.  Then run the following command:

```bash
python -m venv myenv
```

This will create a new directory called `myenv` that contains a Python installation and a `Lib` directory that contains the standard library and any additional packages you install.  

To use the virtual environment, you need to "activate" it.  To activate the virtual environment, navigate to the directory that contains the `myenv` folder and run the following command:

```powershell
.\myenv\Scripts\Activate
```

When the virtual environment is activated, the command prompt will change to show the name of the virtual environment.  Any Python commands you run will use the Python installation in the virtual environment, and any packages you install will be installed into the virtual environment.

To deactivate the virtual environment, run the following command:

```powershell
deactivate
```

When the virtual environment is deactivated, the command prompt will return to normal, and any Python commands you run will use the global Python installation and any packages you install will be installed into the global Python environment.

## Managing Packages
Python comes with a package manager called `pip` that you can use to install and manage packages.  When you have a virtual environment activated, any packages you install will be installed into the virtual environment.  

**Note**: If you do not have a virtual environment activated, packages will be installed into the global Python environment, which is not recommended.

To install a package, use the `pip install` command followed by the name of the package.  For example, to install the `requests` package, you would run the following command:

```bash
pip install requests
```

Pip will download the package from the Python Package Index (PyPI) and install it into your virtual environment.  You can also specify a particular version of a package to install by adding `==` followed by the version number.  For example, to install version 2.25.1 of the `requests` package, you would run the following command:

```bash
pip install requests==2.25.1
```

To see a list of all the packages installed in your virtual environment, run the following command:

```bash
pip list
```

As projects get more complex, it can be difficult to keep track of all the packages you need to install.  To help with this, you can create a file called `requirements.txt` that lists all the packages your project depends on.  You can then use the `pip install` command with the `-r` flag to install all the packages listed in the file.  For example, if you have a `requirements.txt` file that looks like this:

```
requests==2.25.1
websockets==12.0
```

You can install all the packages listed in the file by running the following command:

```bash
pip install -r requirements.txt
```

### A note about setup.py
Packages do not need to be published online to be installed in your python environment.  You can use the `pip install` command to install a package from a `setup.py` file by navigating to the directory that contains the `setup.py` file and running the following command:

```bash
pip install .
```

This "Five9-Agent-Sup-REST-API-Python-Pack" is an example of such a package.  If you make changes to the package and want to install the updated version, you can run the following command:

```bash
pip install --upgrade .
```

Alternatively, you can use pip in "editable" mode which allows you to make changes to the package and see the changes reflected immediately when you run the package.  To install a package in editable mode, navigate to the directory that contains the `setup.py` file and run the following command:

```bash
pip install -e .
```

# Running Python Scripts
Python scripts are just text files that contain Python code.  You can run a Python script by passing the name of the script to the `python` command.  For example, if you have a script called `hello.py` that contains the following code:

```python
print("Hello, world!")
```

You can run the script by navigating to the directory that contains the script and running the following command:

```bash
python hello.py
```

## Script arguments
Some of the scripts in this repository take arguments.  You can pass arguments to a script by adding them after the name of the script.  For example, in the examples directory there is a `queue_alert_demo.py` script that accepts many possible arguments that help you run the script in different ways.  Not all scripts accept arguments, and the arguments that are accepted can vary from script to script.  To see the arguments that a script accepts, you can run the script with the `--help` flag.  For example, to see the arguments that the `queue_alert_demo.py` script accepts, you can run the following command:

```bash
python queue_alert_demo.py --help
```
which will produce the following output:

    usage: queue_alert_demo.py [-h] [-u USERNAME] [-p PASSWORD] [-a ACCOUNT_ALIAS] [-s SOCKET_APP_KEY] [-r REGION] [-l LOGGING_LEVEL]

    Run the Five9RestClient with specified parameters.

    options:
    -h, --help            show this help message and exit
    -u USERNAME, --username USERNAME
                            Username for authentication
    -p PASSWORD, --password PASSWORD
                            Password for authentication
    -a ACCOUNT_ALIAS, --account-alias ACCOUNT_ALIAS
                            Account alias to use for looking up credentials in ACCOUNTS dictionary
    -s SOCKET_APP_KEY, --socket-app-key SOCKET_APP_KEY
                            Socket application key
    -r REGION, --region REGION
                            US, CA, LDN, FRK
    -l LOGGING_LEVEL, --logging-level LOGGING_LEVEL
                            Logging level to use

