'''
Ray Klump
Professor and Chair
Computer and Mathematical Sciences
Lewis University
2017-07-28
'''

import ffmpy
import glob
import os
import ftplib

'''
Settings are stored in a configuration file that has the following format.
dir=path\on\local\machine\without\ending\slash
crf=24
server=name.of.server
user=username
passwd=password
folder=folder/on/remote/server/without/ending/slash

The config dictionary stores them as key:value pairs, where the keys are
dir, crf, server, user, passwd, folder (i.e. the keyword that precedes the
equals sign on each line.)

If no config file is found, we exit the program, so the file has to be there.
'''

config = {}
config_file_name = input("Enter the name of the configuration file: ")
try:
    config_file = open(config_file_name,"r")
    for line in config_file:
        parts = line.split("=")
        config[parts[0]] = parts[1].strip()
    config_file.close()
except:
    print("Could not open the config file.")
    exit()
    
'''
If the server is specified in the config file, then we assume the other 
connection information, like the username and password, are also there,
and so we can upload the resulting files. But, the user might not want to 
upload the resulting compressed files even if the server is specfied in the 
config file. So, we ask the user if they want to. The variable can_upload 
records the user's intention to upload or not. If they do want to upload,
then we'll attempt a connection. If we can connect, then can_upload will
remain True; otherwise, it will turn to False, and we'll tell the user they
will have to upload the files manually using winscp or something like that.
'''

if "server" in config.keys():
    can_upload = input("Upload compressed files to remote server? ").strip().lower() == "y"
    if can_upload == True:
        print("Connecting to remote server ...")
        try:
            session = ftplib.FTP(config["server"],config["user"],config["passwd"])
            print("Done connecting to remote server.")
            can_upload = True
        except:
            can_upload = False
            print("Could not connect to the remote server.")
            print("You'll have to upload the compressed files yourself.")

'''
Next, let's compress every mp4 file that is in the config["dir"] directory
that was identified in the config file. We'll list all the *.mp4 files and,
for each, we'll ask the user what to call the reduced one. If the user
wants to skip a file (i.e. not compress it), they'll simply press Enter,
and the program will move on to the next *.mp4 file. After compressing, if
can_upload is True, we'll send the file to the remote server and directory.
'''

print("\n")
file_names = glob.glob("%s\\*.mp4" % config["dir"])
files = {}
for f in file_names:
    print("Input file = %s" % f)
    outfile_name = input("What should I name the output file? (just press enter to skip) ").strip()
    if outfile_name != "":
        files[f] = outfile_name
    else:
        files[f] = ""
    print()
 
       
print("\nNow proceeding to the compression step.\n")
original_files = []
compressed_files = []
for f in files:
    outfile_name = files[f]
    if outfile_name != "":
        outfile = "%s\\%s" % (config["dir"],outfile_name)
        print("Input file = %s" % f)
        #get rid of existing file if there is one
        try:
            os.remove(outfile)
        except:
            pass
        input_params={f:None}
        output_params = {outfile:'-vcodec libx264 -crf %s' % config["crf"]}
        ff=ffmpy.FFmpeg(inputs=input_params,outputs=output_params)
        print(ff.cmd)  # just to verify that it works
        ff.run()
        original_files.append(f)
        compressed_files.append(outfile)
        print("Done compressing %s" % f)
        print("\n")
   
'''
Now let's upload the compressed files to the remote server (if that's what the
user wants to do and can do based on the value of can_upload.
'''  
for f in files:
    if can_upload == True:
        outfile_name = files[f]
        if outfile_name != "":
            outfile = "%s\\%s" % (config["dir"],outfile_name)            
            remote_file = "%s/%s"%(config["folder"],outfile_name)
            print("Now transmitting %s to the remote server as %s." % (outfile,remote_file))
            compressed = open(outfile,"rb")
            try:
                session.storbinary("STOR %s"%remote_file,compressed)
                compressed.close()
            except:
                print("An error occurred while uploading.")
                print("You'll have to upload the compressed files manually.")
                can_upload = False
                session.quit()
   
'''
Now let's do some file cleanup. We'll ask the user if they want to delete the
original (pre-compressed) files. Then, if can_upload is True, meaning we've
copied the compressed files to the remote server, we'll ask the user if they
want to delete the compressed files, too. That will keep the directory where
the recordings are stored clean so that we can easily run this script again
on the next day's recordings.
'''

should_delete = input("Delete original files? ").strip().lower()
if should_delete == "y":
    for f in original_files:
        os.remove(f)
if can_upload == True:
    session.quit()
    should_delete = input("Delete compressed files? ").strip().lower()
    if should_delete == "y":
        for f in compressed_files:
            os.remove(f)

print("Done!")