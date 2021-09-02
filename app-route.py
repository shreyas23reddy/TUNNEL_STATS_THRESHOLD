
"""
import all the reqiured librariers
"""

import requests
import json
from itertools import zip_longest
import difflib
import sys
import os
import time
import yaml
from smtplib import SMTP
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pretty_html_table import build_table

from auth_header import Authentication as auth
from operations import Operation 



def url(vmanage_host,vmanage_port,api):
    """ return the URL for the privide API ENDpoint """
    """ function to get the url provide api endpoint """
    
    return f"https://{vmanage_host}:{vmanage_port}{api}"




def get_device_info(header):
    """ return the device info of the availble Egde on SDWAN overlay """
    """ used to extract system-ip using the device info"""
    """ function to get the device info """
    
    api_device_info = '/dataservice/device'
    url_device_info = url(vmanage_host,vmanage_port,api_device_info)
    device_info = Operation.get_method(url_device_info, header)

    return device_info['data']



def get_app_stats(system_ip, header):
    """ return the app-stats of the privided Egde system-ip """
    """ provides all the details of APP-route stats for the BFD tunnels for the provided system-ip """
    """ function to get app-stats """


    api_app_stats = '/dataservice/device/app-route/statistics?deviceId=' + system_ip
    url_app_stats = url(vmanage_host,vmanage_port,api_app_stats)
    tunnel_app_stats = Operation.get_method(url_app_stats, header)

    return tunnel_app_stats['data']




def send_email(sender_email, mail_passwd, receiver_email, body):

    """ return if email is sent successful or not"""
    """ function to sent email """

    
    message = MIMEMultipart()
    message['Subject'] = "Real-Time SLA stats beraching the set Thresold"

    body_content = body
    message.attach(MIMEText(body_content, "html"))
    msg_body = message.as_string()

    server = SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, mail_passwd)
    try:
        server.sendmail(sender_email, receiver_email, msg_body)
        return ('email sent')
    except:
        return ('error sending mail')

    server.quit()







if __name__=='__main__':

    """ open the yaml file where the constant data is stored"""

    with open("vmanage_login.yaml") as f:
        config = yaml.safe_load(f.read())
    
    """ Creating a dataset dict"""
    device_dataset = {'Hostname':[], 'system-ip': [], 'remote-system-ip':[] ,'local-color' : [], 'remote-color':[] , 'mean-loss': [], 'mean-latency':[], 'mean-jitter':[]}
    
    """ extracting info from Yaml file"""
    vmanage_host = config['vmanage_host']
    vmanage_port = config['vmanage_port']
    username = config['vmanage_username']
    password = config['vmanage_password']

    mean_loss_threshold = config['mean_loss_threshold']
    mean_latency_thresold = config['mean_latency_thresold']
    mean_jitter_thresold = config['mean_jitter_thresold']


    """ Calling the header function from Auth to get token and cokkie """
    header = auth.get_header(vmanage_host, vmanage_port,username, password)


    """ calling get_device_info function """
    device_details = get_device_info(header)

    """ Iterating through return data from get_device_info function """
    """ match only on vedge device type """
    """ call get_app_stats from the extracted system-ip """
    """ iterate trough all the BFD tunnel and if the stats are breaching the set thresold return the data"""
    """ retrun data is parse into devive_dataset"""
    for individual_device_info in device_details:
        
        if individual_device_info['device-type'] == 'vedge':
            
            tunnel_app_stats = get_app_stats(individual_device_info['system-ip'], header)
            
            for individual_tunnel_stats in tunnel_app_stats:
                
                if (individual_tunnel_stats['mean-loss'] > mean_loss_threshold) or (individual_tunnel_stats['mean-latency'] > mean_latency_thresold) or (individual_tunnel_stats['mean-jitter'] > mean_jitter_thresold):
                    

                    device_dataset['Hostname'].append(individual_device_info['host-name'])
                    device_dataset['system-ip'].append(individual_device_info['system-ip'])
                    device_dataset['remote-system-ip'].append(individual_tunnel_stats['remote-system-ip'])
                    device_dataset['local-color'].append(individual_tunnel_stats['local-color'])
                    device_dataset['remote-color'].append(individual_tunnel_stats['remote-color'])
                    device_dataset['mean-loss'].append(individual_tunnel_stats['mean-loss'])
                    device_dataset['mean-latency'].append(individual_tunnel_stats['mean-latency'])
                    device_dataset['mean-jitter'].append(individual_tunnel_stats['mean-jitter'])


    """ Create DataFrame"""
    data_device = pd.DataFrame(device_dataset)

    """ Convert pandas dataframe to HTML table """
    body = build_table(data_device, 'blue_light')
    

    """ extracting info from Yaml file"""
    sender_email = config['sender_email']
    receiver_email = config['receiver_email']
    mail_password = config['mail_password']

    """ call sen_email """
    print(send_email(sender_email, mail_password, receiver_email, body))
   

