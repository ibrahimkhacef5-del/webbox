cat > setup.py << 'ENDOFFILE'
from setuptools import setup, find_packages

setup(
    name="webbox",
    version="2.1.0",
    description="Site downloader for Termux & Linux",
    author="ibrahimkhacef5-del",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "urllib3>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "webbox=webbox.cli:main",
        ],
    },
    python_requires=">=3.8",
)
ENDOFFILE
