#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
 Copyright (C) 2016 Eleven Paths
 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU Lesser General Public
 License as published by the Free Software Foundation; either
 version 2.1 of the License, or (at your option) any later version.
 This library is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 Lesser General Public License for more details.
 You should have received a copy of the GNU Lesser General Public
 License along with this library; if not, write to the Free Software
 Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""

import hashlib
import os.path
import sys
import pefile
import datetime
import sqlite3
import argparse


class PESecurityCheck:
   
    # DllCharacteristics    
    IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA = 0x0020  # High Entropy ASLR 64bit
    IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE = 0x0040  # ASLR
    IMAGE_DLLCHARACTERISTICS_FORCE_INTEGRITY = 0x0080  # Signature verification
    IMAGE_DLLCHARACTERISTICS_NX_COMPAT = 0x0100  # DEP
    IMAGE_DLLCHARACTERISTICS_NO_ISOLATION = 0x0200
    IMAGE_DLLCHARACTERISTICS_NO_SEH = 0x0400  # SEH
    IMAGE_DLLCHARACTERISTICS_NO_BIND = 0x0800      
    IMAGE_DLLCHARACTERISTICS_APPCONTAINER = 0x1000
    IMAGE_DLLCHARACTERISTICS_WDM_DRIVER = 0x2000  
    IMAGE_DLLCHARACTERISTICS_GUARD_CF = 0x4000  # CFG
    IMAGE_DLLCHARACTERISTICS_TERMINAL_SERVER_AWARE = 0x8000

    def __init__(self, pe):
        self.pe = pe
        
    def highEntropy(self):
        return bool(self.pe.OPTIONAL_HEADER.DllCharacteristics & self.IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA)    

    def aslr(self):
        return bool(self.pe.OPTIONAL_HEADER.DllCharacteristics & self.IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE)

    def forceIntegrity(self):
        return bool(self.pe.OPTIONAL_HEADER.DllCharacteristics & self.IMAGE_DLLCHARACTERISTICS_FORCE_INTEGRITY)

    def dep(self):
        return bool(self.pe.OPTIONAL_HEADER.DllCharacteristics & self.IMAGE_DLLCHARACTERISTICS_NX_COMPAT)

    def noIsolation(self):
        return bool(self.pe.OPTIONAL_HEADER.DllCharacteristics & self.IMAGE_DLLCHARACTERISTICS_NO_ISOLATION)

    def seh(self):
        return bool(self.pe.OPTIONAL_HEADER.DllCharacteristics & self.IMAGE_DLLCHARACTERISTICS_NO_SEH)

    def noBind(self):
        return bool(self.pe.OPTIONAL_HEADER.DllCharacteristics & self.IMAGE_DLLCHARACTERISTICS_NO_BIND)

    def appContainer(self):
        return bool(self.pe.OPTIONAL_HEADER.DllCharacteristics & self.IMAGE_DLLCHARACTERISTICS_APPCONTAINER)

    def wmdDriver(self):
        return bool(self.pe.OPTIONAL_HEADER.DllCharacteristics & self.IMAGE_DLLCHARACTERISTICS_WDM_DRIVER)
        
    def cfg(self):
        return bool(self.pe.OPTIONAL_HEADER.DllCharacteristics & self.IMAGE_DLLCHARACTERISTICS_GUARD_CF)
    
    def terminalServerAware(self):
        return bool(self.pe.OPTIONAL_HEADER.DllCharacteristics & self.IMAGE_DLLCHARACTERISTICS_TERMINAL_SERVER_AWARE)


def get_arch_string(arch):
    if arch == 332:  # IMAGE_FILE_MACHINE_I386 = 0x014c
        return "I386"
    elif arch == 512:  # IMAGE_FILE_MACHINE_IA64 = 0x0200
        return "IA64"
    elif arch == 34404:  # IMAGE_FILE_MACHINE_AMD64 = 0x8664
        return "AMD64"
    else:
        return "Unknown architecture"


def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """

    format_str = "{0:." + str(decimals) + "f}"
    percents = format_str.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '#' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


def print_statistics(dict_results):
    num_files = dict_results.get('num_files')

    num_files_ini = dict_results.get('num_files_ini')
    percent_failed = (num_files_ini - num_files) / num_files_ini * 100

    percent_exe = (dict_results.get('num_exe') / float(dict_results.get('num_files'))) * 100
    percent_dll = (dict_results.get('num_dll') / float(dict_results.get('num_files'))) * 100

    percent_i386 = (dict_results.get('num_i386') / float(dict_results.get('num_files'))) * 100
    percent_amd64 = (dict_results.get('num_amd64') / float(dict_results.get('num_files'))) * 100
    percent_ia64 = (dict_results.get('num_ia64') / float(dict_results.get('num_files'))) * 100
    percent_other = (dict_results.get('num_other_arch') / float(dict_results.get('num_files'))) * 100

    percent_aslr = (dict_results.get('num_aslr') / float(dict_results.get('num_files'))) * 100
    percent_dep = (dict_results.get('num_dep') / float(dict_results.get('num_files'))) * 100
    percent_seh = (dict_results.get('num_seh') / float(dict_results.get('num_files'))) * 100
    percent_cfg = (dict_results.get('num_cfg') / float(dict_results.get('num_files'))) * 100
    percent_highEntropy = (dict_results.get('num_high_entropy') / float(dict_results.get('num_files'))) * 100
    percent_forceIntegrity = (dict_results.get('num_force_integrity') / float(dict_results.get('num_files'))) * 100
    percent_noIsolation = (dict_results.get('num_no_isolation') / float(dict_results.get('num_files'))) * 100
    percent_noBind = (dict_results.get('num_no_bind') / float(dict_results.get('num_files'))) * 100
    percent_appcontainer = (dict_results.get('num_appcontaier') / float(dict_results.get('num_files'))) * 100
    percent_wdmDriver = (dict_results.get('num_wdm_driver') / float(dict_results.get('num_files'))) * 100
    percent_TerminalServerAware = (dict_results.get('num_terminal_server_aware') / float(dict_results.get('num_files'))) * 100

    print("\n\nRESULTS:\n------------------------------------------------------------------------------")
    print("Total files analyzed : " + str(dict_results.get('num_files')))

    print("\nFile types:")

    print("\n\t\tEXE: %d/%d (%d%c)" % (dict_results.get('num_exe'), num_files, percent_exe, chr(37)))
    print("\t\tDLL: %d/%d (%d%c)" % (dict_results.get('num_dll'), num_files, percent_dll, chr(37)))
    print("\t\tFailed: %d/%d (%d%c)" % ((num_files_ini - num_files), num_files_ini, percent_failed, chr(37)))

    print("\nArchitecture:")

    print("\n\t\tI386: %d/%d (%d%c)" % (dict_results.get('num_i386'), num_files, percent_i386, chr(37)))
    print("\t\tAMD64: %d/%d (%d%c)" % (dict_results.get('num_amd64'), num_files, percent_amd64, chr(37)))
    print("\t\tIA64: %d/%d (%d%c)" % (dict_results.get('num_ia64'), num_files, percent_ia64, chr(37)))
    print("\t\tOther: %d/%d (%d%c)" % (dict_results.get('num_other_arch'), num_files, percent_other, chr(37)))

    print("\nGuards:")

    print("\n\t\tASLR (disabled): %d/%d (%d%c)" % (dict_results.get('num_aslr'), num_files, percent_aslr, chr(37)))
    print("\t\tDEP (disabled): %d/%d (%d%c)" % (dict_results.get('num_dep'), num_files, percent_dep, chr(37)))
    print("\t\tNO_SEH (disabled): %d/%d (%d%c)" % (dict_results.get('num_seh'), num_files, percent_seh, chr(37)))
    print("\t\tCFG (disabled): %d/%d (%d%c)" % (dict_results.get('num_cfg'), num_files, percent_cfg, chr(37)))
    print("\t\tHIGH_ENTROPY (disabled): %d/%d (%d%c)" % (dict_results.get('num_high_entropy'), num_files, percent_highEntropy, chr(37)))
    print("\t\tFORCE_INTEGRITY (disabled): %d/%d (%d%c)" % (dict_results.get('num_force_integrity'), num_files, percent_forceIntegrity, chr(37)))
    print("\t\tNO_ISOLATION (disabled): %d/%d (%d%c)" % (dict_results.get('num_no_isolation'), num_files, percent_noIsolation, chr(37)))
    print("\t\tNO_BIND (disabled): %d/%d (%d%c)" % (dict_results.get('num_no_bind'), num_files, percent_noBind, chr(37)))
    print("\t\tAPP_CONTAINER (disabled): %d/%d (%d%c)" % (dict_results.get('num_appcontaier'), num_files, percent_appcontainer, chr(37)))
    print("\t\tWDM_DRIVER (disabled): %d/%d (%d%c)" % (dict_results.get('num_wdm_driver'), num_files, percent_wdmDriver, chr(37)))
    print("\t\tTERMINAl_SERVER_AWARE (disabled): %d/%d (%d%c)" % (dict_results.get('num_terminal_server_aware'), num_files, percent_TerminalServerAware, chr(37)))

    print("\nFiles without any active guard:\n")

    if len(dict_results.get('risk_files')):
        for rf in dict_results.get('risk_files'):
            print("\t\t" + rf[0])
    else:
        print("\t\tNo files found.")

    print("\n------------------------------------------------------------------------------")


def main(arg_path, arg_analysis_tag):

    continue_exec = True

    path = arg_path
    progress = 0
    num_files_ini = 0

    log_filename = arg_analysis_tag + "__" + str(datetime.datetime.now()).replace(':', '_') + ".log"
    database_name = arg_analysis_tag + "__" + str(datetime.datetime.now()).replace(':', '_') + ".db"

    try:
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()

        sql = "CREATE TABLE if not exists \"file_info\" (" \
              "`id_analysis`	TEXT NOT NULL," \
              "`root_folder`	TEXT NOT NULL," \
              "`file_path`	TEXT NOT NULL," \
              "`file_name`	TEXT NOT NULL," \
              "`file_extension`	TEXT NOT NULL," \
              "`architecture`	TEXT NOT NULL," \
              "`file_hash`	TEXT NOT NULL," \
              "`ASLR`	INTEGER," \
              "`DEP`	INTEGER," \
              "`SEH`	INTEGER," \
              "`CFG`	INTEGER," \
              "`HIGH_ENTROPY`    INTEGER," \
              "`FORCE_INTEGRITY`    INTEGER," \
              "`NO_ISOLATION`    INTEGER," \
              "`NO_BIND`    INTEGER," \
              "`APPCONTAINER`    INTEGER," \
              "`WDM_DRIVER`    INTEGER," \
              "`TERMINAL_SERVER_AWARE`    INTEGER" \
              ");"

        cursor.execute(sql)
        
        
    except Exception as e:

        continue_exec = False

        print("Error in database initialization. Try checking user permissions in this directory." \
              "\n\tError info: " + repr(e))

        with open(log_filename, mode='a') as f_error:
            if conn is None:
                f_error.write(str(datetime.datetime.now()) + " -- Error in database creation/connection: "
                                                             "\n\tError info: " + repr(e) + "\n")
            elif cursor is None:
                f_error.write(str(datetime.datetime.now()) + " -- Error in database cursor retrieving: "
                                                             "\n\tError info: " + repr(e) + "\n")
                conn.close()

    if continue_exec:

        try:

            for folder, subs, files in os.walk(path):

                for filename in files:

                    filename = filename.lower()
                    if filename.endswith('.exe') or filename.endswith('.dll'):
                        num_files_ini += 1

            print("\n%d .EXE and .DLL files found in %s\n" % (num_files_ini, path))

        except Exception as e:
            with open(log_filename, mode='a') as f_error:
                f_error.write(str(datetime.datetime.now()) + " -- Error in files pre-count : "
                                                             "\n\tError info: " + repr(e) + "\n")

        dict_results = {}

        for folder, subs, files in os.walk(path):

            for filename in files:

                filename = filename.lower()

                # TODO: is_exe() and is_dll() functions from pefile could be used instead of extension reading.
                if filename.endswith('.exe') or filename.endswith('.dll'):

                    file_path = os.path.join(folder, filename)

                    # Calculate file hash

                    f = None
                    file_hash = None
                    try:
                        f = open(file_path, 'rb')
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    except Exception as e:
                        with open(log_filename, mode='a') as f_error:
                            f_error.write(str(datetime.datetime.now()) + " -- Error calculating file hash: " + 
                                          file_path + "\n\tError info: " + repr(e) + "\n")

                    finally:
                        if f is not None:
                            f.close()

                    try:
                        if file_hash is not None:
                            sql = "select * from file_info where file_info.file_hash like \"" + file_hash + "\";"

                            cursor.execute(sql)

                            if not cursor.fetchone():
                                pe = pefile.PE(file_path, True)

                                ps = PESecurityCheck(pe)

                                aslr = ps.aslr()
                                dep = ps.dep()
                                cfg = ps.cfg()
                                seh = ps.seh()
                                highEntropy = ps.highEntropy()
                                forceIntegrity = ps.forceIntegrity()
                                noIsolation = ps.noIsolation()
                                noBind = ps.noBind()
                                appContainer = ps.appContainer()
                                wmdDriver = ps.wmdDriver()
                                terminalServerAware = ps.terminalServerAware()
                                
                                extension = filename[-4:]
                                architecture = get_arch_string(pe.FILE_HEADER.__getattribute__('Machine'))

                                pe.close()

                                sql = "INSERT INTO `file_info`(`id_analysis`,`root_folder`,`file_path`,`file_name`," \
                                      "`file_extension`,`architecture`,`file_hash`,`ASLR`,`DEP`,`SEH`,`CFG`,`HIGH_ENTROPY`,`FORCE_INTEGRITY`,`NO_ISOLATION`,`NO_BIND`,`APPCONTAINER`,`WDM_DRIVER`,`TERMINAL_SERVER_AWARE`) " \
                                      "VALUES ('%s',\"%s\",\"%s\",'%s','%s','%s',\"%s\",%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d);" % \
                                      (arg_analysis_tag, path, file_path, filename, extension, architecture,
                                       file_hash, aslr, dep, seh, cfg, highEntropy, forceIntegrity, noIsolation, noBind, appContainer, wmdDriver, terminalServerAware)

                                cursor.execute(sql)

                                conn.commit()

                    except (pefile.PEFormatError, Exception) as  e:
                        with open(log_filename, mode='a') as f_error:
                            f_error.write(str(datetime.datetime.now()) + " -- Error in file: " + file_path + 
                                          "\n\tError info: " + repr(e) + "\n")

                    progress += 1

                    print_progress(progress, num_files_ini, prefix='Progress:', suffix='Complete', bar_length=50)

        # Get data results from database
        try:
            dict_results.update({'num_files_ini': num_files_ini})

            sql = "select * from file_info"
            cursor.execute(sql)
            dict_results.update({'num_files': len(cursor.fetchall())})

            sql = "select * from file_info where file_info.file_extension like '.exe'"
            cursor.execute(sql)
            dict_results.update({'num_exe': len(cursor.fetchall())})

            sql = "select * from file_info where file_info.file_extension like '.dll'"
            cursor.execute(sql)
            dict_results.update({'num_dll': len(cursor.fetchall())})

            sql = "select * from file_info where not file_info.ASLR"
            cursor.execute(sql)
            dict_results.update({'num_aslr': len(cursor.fetchall())})

            sql = "select * from file_info where not file_info.DEP"
            cursor.execute(sql)
            dict_results.update({'num_dep': len(cursor.fetchall())})

            sql = "select * from file_info where not file_info.SEH"
            cursor.execute(sql)
            dict_results.update({'num_seh': len(cursor.fetchall())})

            sql = "select * from file_info where not file_info.CFG"
            cursor.execute(sql)
            dict_results.update({'num_cfg': len(cursor.fetchall())})
            
            sql = "select * from file_info where not file_info.HIGH_ENTROPY"
            cursor.execute(sql)
            dict_results.update({'num_high_entropy': len(cursor.fetchall())})
            
            sql = "select * from file_info where not file_info.FORCE_INTEGRITY"
            cursor.execute(sql)
            dict_results.update({'num_force_integrity': len(cursor.fetchall())})
            
            sql = "select * from file_info where not file_info.NO_ISOLATION"
            cursor.execute(sql)
            dict_results.update({'num_no_isolation': len(cursor.fetchall())})
            
            sql = "select * from file_info where not file_info.NO_BIND"
            cursor.execute(sql)
            dict_results.update({'num_no_bind': len(cursor.fetchall())})
            
            sql = "select * from file_info where not file_info.APPCONTAINER"
            cursor.execute(sql)
            dict_results.update({'num_appcontaier': len(cursor.fetchall())})
            
            sql = "select * from file_info where not file_info.WDM_DRIVER"
            cursor.execute(sql)
            dict_results.update({'num_wdm_driver': len(cursor.fetchall())})
            
            sql = "select * from file_info where not file_info.TERMINAL_SERVER_AWARE"
            cursor.execute(sql)
            dict_results.update({'num_terminal_server_aware': len(cursor.fetchall())})
            
            sql = "select * from file_info where file_info.architecture like 'I386'"
            cursor.execute(sql)
            dict_results.update({'num_i386': len(cursor.fetchall())})

            sql = "select * from file_info where file_info.architecture like 'AMD64'"
            cursor.execute(sql)
            dict_results.update({'num_amd64': len(cursor.fetchall())})

            sql = "select * from file_info where file_info.architecture like 'IA64'"
            cursor.execute(sql)
            dict_results.update({'num_ia64': len(cursor.fetchall())})

            sql = "select * from file_info where file_info.architecture not like 'I386' " \
                  "and file_info.architecture not like 'AMD64'" \
                  "and file_info.architecture not like 'IA64'"
            cursor.execute(sql)
            dict_results.update({'num_other_arch': len(cursor.fetchall())})

            sql = "select file_path from file_info " \
                  "where not file_info.CFG and not file_info.ASLR and not file_info.DEP and not file_info.SEH"
            cursor.execute(sql)
            dict_results.update({'risk_files': cursor.fetchall()})

            print_statistics(dict_results=dict_results)

        except Exception as e:
            with open(log_filename, mode='a') as f_error:
                f_error.write(str(datetime.datetime.now()) + " -- Failed to retrieve statistics from DB: " + 
                              "\n\tError info: " + repr(e) + "\n")
            print("Error: Failed to retrieve statistics from DB\n\tError info: " + repr(e))

        print("\nErrors exported to " + log_filename)

        print("\nExport data? Press:")
        print("\t n -- Don't export")
        print("\t s -- Export to SQL script")
        print("\t c -- Export to CSV file")

        response = input()

        while response != 'n' and response != 's' and response != 'c':
            print('Please, enter a valid option [[n]/[s]/[c]]')
            response = input()

        if response.lower() != 'n':
            # TODO: Check and show export result
            export_filename = database_name = arg_analysis_tag + "__" + str(datetime.datetime.now()).replace(':', '_')

            try:
                sql = "select * from file_info"
                cursor.execute(sql)

                if response.lower() == 'c':
                    print("Exporting to CSV")

                    with open(export_filename + '.csv', mode='a')as f:

                        header = '"id_analysis","root_folder","file_path","file_name",' \
                                 '"file_extension","architecture","file_hash","ASLR",' \
                                 '"DEP","SEH","CFG","HIGH_ENTROPY","FORCE_INTEGRITY",'\
                                 '"NO_ISOLATION","NO_BIND","APPCONTAINER","WDM_DRIVER","TERMINAL_SERVER_AWARE"'

                        f.write(header)

                        for row in cursor.fetchall():
                            w_row = '\n"%s","%s","%s",%s","%s","%s","%s","%d","%d","%d","%d","%d","%d","%d","%d","%d","%d","%d",' % \
                                    (row[0], row[1], row[2], row[3], row[4], row[5],
                                     row[6], row[7], row[8], row[9], row[10],row[11], row[12], row[13], row[14],row[15], row[16], row[17])
                            f.write(w_row)

                if response.lower() == 's':
                    print("Exporting to SQL")
                    with open(export_filename + '.sql', mode='a')as f:
                        sql = "BEGIN TRANSACTION;\n\n" \
                              "CREATE TABLE \"file_info\" (\n" \
                              "\t`id_analysis`	TEXT NOT NULL,\n" \
                              "\t`root_folder`	TEXT NOT NULL,\n" \
                              "\t`file_path`	TEXT NOT NULL,\n" \
                              "\t`file_name`	TEXT NOT NULL,\n" \
                              "\t`file_extension`	TEXT NOT NULL,\n" \
                              "\t`architecture`	TEXT NOT NULL,\n" \
                              "\t`file_hash`	TEXT NOT NULL,\n" \
                              "\t`ASLR`	INTEGER,\n" \
                              "\t`DEP`	INTEGER,\n" \
                              "\t`SEH`	INTEGER,\n" \
                              "\t`CFG`    INTEGER,\n" \
                              "\t`HIGH_ENTROPY`    INTEGER,\n" \
                              "\t`FORCE_INTEGRITY`    INTEGER,\n" \
                              "\t`NO_ISOLATION`    INTEGER,\n" \
                              "\t`NO_BIND`    INTEGER,\n" \
                              "\t`APPCONTAINER`    INTEGER,\n" \
                              "\t`WDM_DRIVER`    INTEGER,\n" \
                              "\t`TERMINAL_SERVER_AWARE `    INTEGER" \
                              ");\n"
                        f.write(sql)

                        for row in cursor.fetchall():
                            w_row = "INSERT INTO `file_info`(`id_analysis`,`root_folder`,`file_path`,`file_name`," \
                                    "`file_extension`,`architecture`,`file_hash`,`ASLR`,`DEP`,`SEH`,`CFG`) " \
                                    "VALUES ('%s',\"%s\",\"%s\",'%s','%s','%s',\"%s\",%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d);" % \
                                    (row[0], row[1], row[2], row[3], row[4], row[5],
                                     row[6], row[7], row[8], row[9], row[10], row[11],
                                     row[12], row[13], row[14], row[15], row[16], row[17])

                            f.write("\n" + w_row)

                        f.write("\n\nCOMMIT;")
            except Exception as e:
                with open(log_filename, mode='a') as f_error:
                    f_error.write(str(datetime.datetime.now()) + " -- Error in data export:" + 
                                  "\n\tError info: " + repr(e) + "\n")

        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

        try:
            os.remove(database_name)
        except Exception as e:
            with open(log_filename, mode='a') as f_error:
                f_error.write(str(datetime.datetime.now()) + " -- Error. Unable to remove database:" + 
                              "\n\tError info: " + repr(e) + "\n")


if __name__ == '__main__':

    print("\nPESTO (c) ElevenPaths. Version: 0.2.0.0\n")

    parser = argparse.ArgumentParser()
    parser.add_argument('directory_path', type=str, help='Directory to analyze.')
    parser.add_argument('analysis_tag', type=str, help='Use any name as tags to identify your investigation.')
    args = parser.parse_args()

    main(arg_path=args.directory_path, arg_analysis_tag=args.analysis_tag)
