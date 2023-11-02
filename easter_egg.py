import seedir as sd
from pathlib import Path
import logging

import jinja2
from jinja2 import Environment, BaseLoader, DictLoader

from easy_configer.Configer import Configer
from easy_configer.IO_Converter import IO_Converter

from collections import defaultdict
import os
import click

class Hatcher:
    def __init__(self, blue_print_root):
        self.bp_rt = Path(blue_print_root)
        self.tmplt_cfg = self.__load_template_config(self.bp_rt)
        self.tmplt_dict = self.__template2dict(self.bp_rt)
        self.proj_struct = self.__load_blue_print(self.bp_rt)
        
    def __load_template_config(self, bp_rt):

        def update_config_by_cmdline(tmplt_cfg):
            cnvt = IO_Converter()
            tmplt_dct = cnvt.cnvt_cfg_to(tmplt_cfg, "dict")

            for key in tmplt_dct.keys():
                val = tmplt_dct[key]
                tmplt_dct[key] = click.prompt(f'Please enter argument {key} [default={val}]\n', default=val)

            return cnvt.cnvt_cfg_from(tmplt_dct, "dict")
            
        cfg_file = list(bp_rt.glob('*.ini'))
        if len(cfg_file) == 0:
            raise RuntimeError("blue print root doesn't contains any .ini file")
        elif len(cfg_file) > 1:
            print("Warning : blue print root contains multiple .ini file, we only take one")
            print(f"{cfg_file[0]} is used to render the template!")
        cfg_file = cfg_file[0]
        tmplt_cfg = Configer()
        tmplt_cfg.cfg_from_ini(cfg_file)
        return update_config_by_cmdline(tmplt_cfg)

    def __template2dict(self, proj_dist):
        tmplt_dct = defaultdict(str)
        idx_dct = dict()
        jdx = 0
        for j, tmplt_file in enumerate( self.bp_rt.rglob('*.tmplt') ):
            with tmplt_file.open('r') as tmplt_pt:
                for line in tmplt_pt:
                    if line.strip().startswith('>'):
                        idx = line.find('@')
                        if idx != -1:
                            tmplt_id = line[idx+1:].strip()
                            raw_tmplt_path = line[1:idx].lstrip()
                            tmplt_path = raw_tmplt_path.format(estEgg=self.tmplt_cfg)
                            idx_dct[tmplt_path] = tmplt_id
                        else:
                            tmplt_id = f"dummy{jdx}"
                            line = line.strip()
                            raw_tmplt_path = line[1:].lstrip()
                            tmplt_path = raw_tmplt_path.format(estEgg=self.tmplt_cfg)
                            idx_dct[tmplt_path] = tmplt_id
                        jdx += 1
                    else:
                        line = line.rstrip()
                        tmplt_dct[tmplt_id]+=(line+'\n')
        
        environment = Environment(
            loader=DictLoader(tmplt_dct),
        )
        for path, tid in idx_dct.items():
            cnt = environment.get_template(tid).render(estEgg=self.tmplt_cfg)
            idx_dct[path] = cnt
        
        return idx_dct

    def __load_blue_print(self, bp_rt):
        bp_file = list(self.bp_rt.glob('*.bp'))
        if len(bp_file) == 0:
            raise RuntimeError("blue print root doesn't contains any .bp file")
        elif len(bp_file) > 1:
            print("Warning : blue print root contains multiple .bp file, we only take one")
            print(f"{bp_file[0]} is used to build the project!")
        bp_file = bp_file[0]

        with bp_file.open('r') as bp_ptr:
            fd_struct_str = ""
            for raw_strlin in bp_ptr:
                if "{" in raw_strlin:
                    strlin = raw_strlin.format(estEgg=self.tmplt_cfg)
                else:
                    strlin = raw_strlin
                fd_struct_str += strlin
        
        return sd.fakedir_fromstring(fd_struct_str, parse_comments=True)

    def hatch_egg(self, proj_dist='./', preview=True, preview_path='./proj_struct', preview_style='emoji'):
        
        def save_fd_struct(proj_struct_str):
            with open(preview_path, 'w+', encoding='utf-8') as f_ptr:
                f_ptr.writelines(proj_struct_str)

        # it should save the preview after name-rendering
        proj_raw_str = self.proj_struct.seedir(style='lines', printout=False)
        # project root string with strip backslash..
        proj_rt = proj_raw_str.split('\n')[0]  
        
        if preview:
            proj_struct_str = self.proj_struct.seedir(style=preview_style, printout=False)
            render_struct = proj_struct_str.format(estEgg=self.tmplt_cfg)
            save_fd_struct(render_struct)

        self.proj_struct.realize(proj_dist)
        for path, data in self.tmplt_dict.items():
            path = proj_dist / Path(path)
            with path.open('w') as f_ptr:
                f_ptr.writelines(data)

@click.command()
@click.option('-r', '--blue-print-root', default='./', type=str, show_default=True)
@click.option('-d', '--proj-dist', default='./', type=str, show_default=True)
@click.option('-p', '--preview', default=True, type=bool, show_default=True)
def easter_egg(blue_print_root, proj_dist, preview):
    hatchr = Hatcher(blue_print_root)
    print("Hatching easter-egg...\n")
    hatchr.hatch_egg(proj_dist=proj_dist, preview=preview)
    print(f"After project building : {os.listdir(os.getcwd())}\n")


if __name__ == "__main__":
    easter_egg()