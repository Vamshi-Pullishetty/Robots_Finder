# Robots_Finder
A simple tool to quickly locate and retrieve robots.txt files from websites. Useful for ethical hacking, SEO analysis, and web development, this tool helps users understand which parts of a website are accessible to web crawlers. Supports batch processing and customizable user agents for effective scanning.

# Features

- Retrieve historical robots.txt files from Archive.org.
- Display previously disallowed paths and directories.
- Save search results to a file.
- Run the tool without console output (silent mode).
- Speed up searches with adjustable multi-threading.

# Installation
Clone the repository and install the required dependencies:

```
git clone https://github.com/Vamshi-Pullishetty/Robots_Finder.git
cd Robots_Finder
pip install -r requirements.txt
```

# Usage
Run the program by providing a URL with the -u flag:

```
python3 robot.py -u https://example.com
```

# Additional Options
- Save output to file:
```
python3 robot.py -u https://example.com -o results.txt
```

- Concatenate paths with site URL:
```
python3 robot.py -u https://example.com -c
```

- Run in silent mode (no console output):
```
python3 robot.py -u https://example.com --silent
```

- Multi-threading (default recommended: 10 threads):
```
python3 robot.py -u https://example.com -t 10 -c -o results.txt
```

# Example
To run Robofinder on https://example.com and save the result to results.txt with 10 threads:
```
python3 robot.py -u https://example.com -t 10 -o results.txt
```











