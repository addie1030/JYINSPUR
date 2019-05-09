from odoo import http
from odoo.http import request
import os
# from tkinter import *
# import tkinter.filedialog
# import tkinter as tk
import odoo

class statement_import(http.Controller):
    def find_last(self,fname,str):
        last_position=-1
        while True:
            position=fname.find(str,last_position+1)
            if position==-1:
                return last_position
            last_position=position
    @http.route('/odoo/import_file', auth='public', type='json', method='POST')
    def import_file(self):
        return []
        # # filenames = tkinter.filedialog.askopenfilenames()
        # # if len(filenames) != 0:
        # #     string_filename = ""
        # #     for i in range(0, len(filenames)):
        # #         string_filename += str(filenames[i]) + "\n"
        # #     print(string_filename)
        # # else:
        # #     print("您没有选择任何文件")
        #
        # root = tk.Tk()
        # root.withdraw()
        #
        # # default_dir = r"C:\Users\lenovo\Desktop"  # 设置默认打开目录
        # # default_dir = r"/"  # 设置默认打开目录
        # # with odoo.tools.osutil.tempdir() as dump_dir:
        # #     fname = tkinter.filedialog.askopenfilename(title=u"选择文件",initialdir=(os.path.expanduser(dump_dir)))
        # #     fname = fname[2:len(fname)]
        #
        # path = os.getcwd()
        # fname = tkinter.filedialog.askopenfilename(title=u"选择文件",initialdir=(os.path.expanduser(path)))
        # fname = fname[2:len(fname)]
        #
        # if len(fname) > 0:
        #     with open(fname, 'r') as f:
        #         list1 = f.readlines()
        #     for i in range(0, len(list1)):
        #         list1[i] = list1[i].strip('\n')
        #
        #     jsonstr = list1[0]
        #     name = "资产负债表"
        #     last_position = self.find_last(fname,"_")
        #     name = fname[last_position+1:len(fname)-7]
        #
        #     return [jsonstr,name]


# from odoo import http
# import paramiko
# import datetime
# import os
#
# hostname = '10.24.35.5'
# username = 'root'
# password = 'Test6530'
# port = 22
#
# class statement_import(http.Controller):
#     @http.route('/odoo/import_file', auth='public', type='json', method='POST')
#     def import_file(self):
#         local_dir = r'D:\111'
#         remote_dir = '/home/share/111/'
#         try:
#             t = paramiko.Transport((hostname, port))
#             t.connect(username=username, password=password)
#             sftp = paramiko.SFTPClient.from_transport(t)
#             print('upload file start %s ' % datetime.datetime.now())
#             for root, dirs, files in os.walk(local_dir):
#                 print('[%s][%s][%s]' % (root, dirs, files))
#                 for filespath in files:
#                     local_file = os.path.join(root, filespath)
#                     print(11, '[%s][%s][%s][%s]' % (root, filespath, local_file, local_dir))
#                     a = local_file.replace(local_dir, '').replace('\\', '/').lstrip('/')
#                     print('01', a, '[%s]' % remote_dir)
#                     remote_file = os.path.join(remote_dir, a)
#                     print(22, remote_file)
#                     try:
#                         sftp.put(local_file, remote_file)
#                     except Exception as e:
#                         sftp.mkdir(os.path.split(remote_file)[0])
#                         sftp.put(local_file, remote_file)
#                         print("66 upload %s to remote %s" % (local_file, remote_file))
#                 for name in dirs:
#                     local_path = os.path.join(root, name)
#                     print(0, local_path, local_dir)
#                     a = local_path.replace(local_dir, '').replace('\\', '')
#                     print(1, a)
#                     print(1, remote_dir)
#                     remote_path = os.path.join(remote_dir, a)
#                     print(33, remote_path)
#                     try:
#                         sftp.mkdir(remote_path)
#                         print(44, "mkdir path %s" % remote_path)
#                     except Exception as e:
#                         print(55, e)
#             print('77,upload file success %s ' % datetime.datetime.now())
#             t.close()
#         except Exception as e:
#             print(88, e)

