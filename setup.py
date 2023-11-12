from setuptools import setup

setup(
    name='labpack',
    version='3.0.0',
    description='Lab-specific stimuli to be used with stimpack',
    url='https://github.com/ClandininLab/labpack',
    author='Max Turner, Minseung Choi',
    author_email='mhturner@stanford.edu, minseung@stanford.edu',
    packages=['labpack'],
    install_requires=[
        'nidaqmx',
        'hidapi',
        'labjack-ljm',
        'icosphere'],
    include_package_data=True,
    zip_safe=False,
)
