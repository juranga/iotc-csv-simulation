# Simulate Device Data from CSV files in Azure IoT Central

TODO: Need to update DeviceData/DeviceModels and figure out best way to generalize this.

## Introduction
This repository contains the necessary start-up code to simulate IoT Devices in [Azure IoT Central](https://azure.microsoft.com/en-us/services/iot-central/) from pre-defined csv files, and it comes pre-packaged with sample simulated Energy and Power devices to facilitate getting started.

Deploying this repository will create the following resources in your subscription:
1. Resource Group 
1. IoT Central Application
1. Storage Account
    * Blob Storage
    * Azure Table
1. App Service
1. Azure Function

If you already have any of the resources specified above, please follow the instructions in [Connecting Pre-Existing Azure Resources](#connecting-pre-existing-azure-resources).

## Getting Started
You will need the following items to run this deployment:
1. Install [Python 3.7.1](https://www.python.org/downloads/release/python-371/) <br />
2. An Azure Subscription id

To obtain an Azure Subscription id, visit the [Azure Portal](https://portal.azure.com) and search for `Subscriptions` in the search bar. Select a valid subscription from the list of available subscriptions and copy its corresponding id. You will need it in the steps below.

Once the id has been obtained, edit the `Deploy.py` file found in this directory and populate the `subscription_id` variable with this id. Optionally, you can enter the subscription id as a parameter when running the Deploy script as shown in the [Deploying Section](#Deploying). <br />

All resources will be deployed in to a resource group titled **iotcustomsimulation** under the subscription desired.

## Customizing your Deployment

#### Connecting Pre-Existing Azure Resources

Any pre-existing Azure Resource that you would like to reuse can be easily specified by navigating to the `default.params.json` file under the *Templates* folder in the current directory. 

#### Plugging in your own csv files TODO:UPDATE THIS AREA
Customizing this solution is as easy as dropping your device csv files in to the *DeviceDataCSVs* folder and editing the corresponding **DeviceModels.csv** file found under the *DeviceTypes* folder in the *Data* folder to begin simulating the number of devices desired. Do make sure your device csv files follow the same structure as the already defined device csv data files. <br />

* An example of the structure required for your device csv data files can be found in **SampleCSVData.csv** file under the *Data* Folder.
* An example of how you would edit the **DeviceTypes.csv** file can be seen in the SampleDeviceType.csv file under the *Data* Folder.

It is highly recommended to only simulate 100 devices, as this solution is not optimized for scaling. <br />
If you would like to simulate more than 100 devices for scale tests in IoT Central, contact the Azure IoT Central ORCA folks.

### Deploying 

After the above requirements have been met, open your favorite shell and run the following commands:
Note, this may take a long time as it is installing dependencies the project needs & deploying Azure resources.

`pip install -r requirements.txt` <br />
`python Deploy.py <subscription id>`