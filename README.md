# Simulate Device data from CSV files in Azure IoT Central

### Introduction
This Repository contains the necessary start-up code to begin simulating IoT Devices in [Azure IoT Central](https://azure.microsoft.com/en-us/services/iot-central/) from pre-defined csv files, and comes equipped with sample Energy and Power Device simulation data to get you started. <br />

Do note however, that there is a predefined simulated device limitation of 100 devices, as this solution is designed to make simulating real devices as cheap as possible. <br />
It is advised that if you would like to simulate more than 100 devices for scale tests in Central, you should contact the Azure IoT Central ORCA folks.

**NOTE: Initial costs when deploying this solution with 100 simulated devices falls below $5 a month.**

### Getting Started
You will need the following items to run this deployment:
1. Install [Python 3.7.1](https://www.python.org/downloads/release/python-371/) <br />
1. An Azure Subscription id

To obtain an Azure Subscription id, talk to your manager or visit the [Azure Portal](https://portal.azure.com) & search for `Subscriptions` in the search bar. <br />
Select a valid subscription and copy its corresponding id. You will need it for the step below.

Once obtained, edit the `Deploy.py` file found in this directory and populate the `subscription_id` variable with this id. <br />
Optionally, you can enter the subscription id as a parameter when running the Deploy script as shown in the [Deploying Section](#Deploying). <br />

### Customizing your Deployment
Customizing this solution is as easy as dropping your device csv files in to the *DeviceDataCSVs* folder and editing the corresponding **DeviceTypes.csv** file found under the *DeviceTypes* folder in the *Data* folder to begin simulating the number of devices desired. Do make sure your device csv files follow the same structure as the already defined device csv data files. <br />

* An example of the structure required for your device csv data files can be found in **SampleCSVData.csv** file under the *Data* Folder.
* An example of how you would edit the **DeviceTypes.csv** file can be seen in the SampleDeviceType.csv file under the *Data* Folder.

### Deploying 

After the above requirements have been met, open up your favorite shell and run the following commands:

`pip install -r requirements.txt` <br />
`python Deploy.py <subscription id> `