'''
Configuration을 관리하고 초기화하는 클래스를 제공
'''


import re
import os
import yaml
import torch
from logging import getLogger


class Config(object):
    """
    Configuration을 로드하고 관리하는 클래스
    """
    def __init__(self, model=None, dataset=None, config_dict=None):
        """
        클래스 초기화: 설정 파일을 로드하고, 기본 설정을 적용
        """
        # load dataset config file yaml
        if config_dict is None:
            config_dict = {}
        config_dict['model'] = model
        config_dict['dataset'] = dataset
        # model type
        self.final_config_dict = self._load_dataset_model_config(config_dict)
        # config in cmd and main.py are latest
        self.final_config_dict.update(config_dict)
        self._set_default_parameters()
        self._init_device()


    def _load_dataset_model_config(self, config_dict):
        """
        configuration 파일 (.yaml)을 로드하여 파라미터를 결합
        """
        file_config_dict = dict()
        file_list = []
        # get dataset and model files
        cur_dir = os.getcwd()
        cur_dir = os.path.join(cur_dir, 'configs')
        file_list.append(os.path.join(cur_dir, "overall.yaml"))
        file_list.append(os.path.join(cur_dir, "dataset", "{}.yaml".format(config_dict['dataset'])))
        file_list.append(os.path.join(cur_dir, "model", "{}.yaml".format(config_dict['model'])))

        hyper_parameters = []
        for file in file_list:
            if os.path.isfile(file):
                with open(file, 'r', encoding='utf-8') as f:
                    fdata = yaml.load(f.read(), Loader=self._build_yaml_loader())
                    if fdata.get('hyper_parameters'):
                        hyper_parameters.extend(fdata['hyper_parameters'])
                    file_config_dict.update(fdata)
                    
        file_config_dict['hyper_parameters'] = hyper_parameters
        return file_config_dict


    def _build_yaml_loader(self):
        loader = yaml.FullLoader
        loader.add_implicit_resolver(
            u'tag:yaml.org,2002:float',
            re.compile(u'''^(?:
             [-+]?(?:[0-9][0-9_]*)\\.[0-9_]*(?:[eE][-+]?[0-9]+)?
            |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)
            |\\.[0-9_]+(?:[eE][-+][0-9]+)?
            |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\\.[0-9_]*
            |[-+]?\\.(?:inf|Inf|INF)
            |\\.(?:nan|NaN|NAN))$''', re.X),
            list(u'-+0123456789.'))
        return loader


    def _set_default_parameters(self):
        """
        Configuration에서 기본적으로 사용할 파라미터를 설정
        """
        smaller_metric = ['rmse', 'mae', 'logloss']
        valid_metric = self.final_config_dict['valid_metric'].split('@')[0]
        self.final_config_dict['valid_metric_bigger'] = False if valid_metric in smaller_metric else True
        # if seed not in hyper_parameters, then add
        if "seed" not in self.final_config_dict['hyper_parameters']:
            self.final_config_dict['hyper_parameters'] += ['seed']

    
    def _init_device(self):
        """
        실행에 사용할 디바이스(GPU/CPU)를 초기화
        """
        use_gpu = self.final_config_dict['use_gpu']
        if use_gpu:
            os.environ["CUDA_VISIBLE_DEVICES"] = str(self.final_config_dict['gpu_id'])
        self.final_config_dict['device'] = torch.device("cuda" if torch.cuda.is_available() and use_gpu else "cpu")


    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError("index must be a str.")
        self.final_config_dict[key] = value


    def __getitem__(self, item):
        if item in self.final_config_dict:
            return self.final_config_dict[item]
        else:
            return None


    def __contains__(self, key):
        if not isinstance(key, str):
            raise TypeError("index must be a str.")
        return key in self.final_config_dict


    def __str__(self):
        """
        설정 값을 문자열로 출력
        """
        args_info = '\n'
        args_info += '\n'.join(["{}={}".format(arg, value) for arg, value in self.final_config_dict.items()])
        args_info += '\n\n'
        return args_info


    def __repr__(self):
        return self.__str__()