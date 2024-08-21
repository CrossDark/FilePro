"""
用于切换不同的文件组
"""
import os
import platform
import re
import shutil
import subprocess
import time
from typing import *

import ruamel.yaml

base_dir = os.getcwd()  # 获取运行路径
system = platform.system()  # 获取运行系统


def ignore(file_name: str) -> bool:
    """
    判断是否忽略该文件
    :param file_name: 待判断的文件名
    :return: 是否该被忽略
    """
    if file_name.startswith('.'):  # 隐藏文件
        return False
    if file_name in ('Icon', 'Icon'):  # MAC图标文件
        return False
    return True


def make_settings(file_path: str):
    """
    创建设置文件
    :param file_path: 设置文件路径
    """
    with open(file_path, 'w') as file:
        file.write("""
always:
    .内容/.always
cache:
    .内容/.cache
path:
    .内容/(你选定的目录)
        """)


def read_yaml(path) -> Tuple[str, str, str]:
    """
    读取设置yaml并移除被<>扩起来的注释
    :param path: 设置文件路径
    :return: 永久保留文件目录、缓存文件目录、选定文件目录
    """
    with open(path, encoding='utf-8') as file:
        settings = ruamel.yaml.YAML(typ='safe').load(re.sub('<[^>]*>', '', file.read()))
    return settings['always'], settings['cache'], settings['path']


def cleanup_symlinks():
    """
    删除当前目录下的所有符号链接。
    :return:
    """
    if base_dir.startswith('.') and base_dir != '.':
        return
    for item in os.listdir(base_dir):
        if os.path.islink(os.path.join(base_dir, item)):
            os.unlink(os.path.join(base_dir, item))
            print(f'”{item}“清理成功')
        else:
            print(f'“{item}”不是链接')


def clean_directory_links(directory_path: str):
    """
    清空指定目录中的所有文件和子目录（包括非目录的符号链接），但不删除目录本身。
    :param directory_path: 要清空的目录的路径
    """
    # 确保目录存在
    if not os.path.exists(directory_path):
        print(f"目录“{directory_path}”不存在。")
        return
    # 遍历目录中的所有项
    for item_name in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item_name)
        shutil.rmtree(directory_path)
        os.mkdir(directory_path)
        print(f'"{item_path}"已清除')


def clean_links_only(directory_path: str):
    """
    只清空指定目录中的符号链接，不删除目录本身。
    :param directory_path: 要清空的目录的路径
    """
    # 确保目录存在
    if not os.path.exists(directory_path):
        print(f"目录“{directory_path}”不存在。")
        return
    # 遍历目录中的所有项
    for item_name in os.listdir(directory_path):
        if os.path.islink(os.path.join(directory_path, item_name)): # 判断是否为链接文件
            os.unlink(os.path.join(directory_path, item_name))
            print(f'"{os.path.join(directory_path, item_name)}"解除链接成功')
        else:
            print(f'"{os.path.join(directory_path, item_name)}"不是链接')


def list_files(directory: str, mode: str = 'all') -> Union[List, bool]:
    """
    列出给定目录下符合要求的目录
    :param directory: 要查找的目录
    :param mode: 模式
    :return: 如果目录存在,返回目录下符合要求的文件列表,否则返回False
    """
    # 确保给定的目录存在
    if not os.path.exists(directory):
        print(f"指定的目录“{directory}”不存在。")
        return False
    if mode == 'all':  # 获取给定目录的文件列表
        return [d for d in os.listdir(directory) if ignore(d)]
    if mode == 'immediate':  # 获取给定目录的直接子目录列表
        return [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    if mode == 'links':  # 获取给定目录的链接文件列表
        return [d for d in os.listdir(directory) if os.path.islink(os.path.join(directory, d))]


def make_symlinks(src: str, dst: str, files: List[str]):
    """
    将src内的指定文件files链接到dst
    :param src: 源目录
    :param dst: 目标目录
    :param files: 要链接的文件列表
    :return:
    """
    for file in files:
        try:
            os.symlink(os.path.abspath(os.path.join(src, file)), os.path.abspath(os.path.join(dst, file)))
        except FileExistsError:  # 文件已经存在
            print(f'“{os.path.join(dst, file)}”链接已经存在')
        except FileNotFoundError:
            print(f'"{os.path.join(dst, file)}"不存在')
        else:  # 创建成功
            print(f'“{os.path.join(dst, file)}”链接成功')


def make_deep_symlinks(src: str, dst: str, dirs: List[str]):
    """
    将src内的指定目录dirs中的所有文件分别链接到dst
    :param src: 源目录
    :param dst: 目标目录
    :param dirs: 要链接的目录
    :return:
    """
    for file in dirs:
        src_files = list_files(os.path.join(src, file))
        if not src_files:
            continue
        for inside_file in src_files:
            try:
                os.symlink(os.path.abspath(
                    os.path.join(src, file, inside_file)), os.path.abspath(os.path.join(dst, file, inside_file))
                )
            except FileExistsError:  # 文件已经存在
                print(f'“{os.path.join(file, inside_file)}”链接已经存在')
            except FileNotFoundError:
                print(f'"{os.path.join(file, inside_file)}"不存在')
            else:  # 创建成功
                print(f'“{os.path.join(file, inside_file)}”链接成功')


def make_dirs(dst: str, dirs: List[str]):
    """
    根据给定的文件列表在dst目录中创建子目录
    :param dst: 目标目录
    :param dirs: 要创建的子目录
    :return:
    """
    for dir_ in dirs:
        os.mkdir(os.path.join(dst, dir_))
        print(f'"{os.path.join(dst, dir_)}"创建成功')


def is_on_unix_network_volume(path: str) -> bool:
    """
    判断UNIX上的文件是否在网络驱动器上
    :param path: 待判断的文件
    :return: 如果在网络驱动器上,返回True,否则返回False
    """
    df_output = subprocess.check_output(['df', path]).decode('utf-8').split('\n')[1:]
    if len(df_output) >= 1:
        # 第一行是标题，第二行包含了文件系统类型
        fs_type = df_output[0].split('  ')
        if fs_type[0].startswith('//'):
            return True
        else:
            return False


def main():
    """
    主函数
    :return:
    """
    print('加载设置')
    try:
        always, cache, path = read_yaml(os.path.join(base_dir, '.FileSwitcher.yaml'))
    except FileNotFoundError:
        make_settings(os.path.join(base_dir, '.FileSwitcher.yaml'))
        return

    print('清除之前选定的文件中的链接')
    for folder in list_files(base_dir, mode='links'):
        clean_links_only(os.path.join(base_dir, folder))

    print('清除缓存')
    clean_directory_links(os.path.join(base_dir, cache))

    print('清除之前的链接')
    cleanup_symlinks()

    print('获取选定目录')
    paths = list_files(os.path.join(base_dir, path), mode='immediate')

    print('链接永久保留文件到选定文件夹')
    make_deep_symlinks(os.path.join(base_dir, always), os.path.join(base_dir, path), paths)

    print('链接选定文件夹到当前目录')
    make_symlinks(os.path.join(base_dir, path), base_dir, paths)


if __name__ == '__main__':
    if system in ('Darwin', 'Linux'):  # 如果文件在网络驱动器上,则需要在NAS上运行
        if is_on_unix_network_volume(base_dir):
            raise SystemError('文件在网络驱动器上,需要在NAS上运行此代码')
    elif system == 'Windows':
        pass
    else:
        raise SystemError(f'"{system}"什么奇妙的操作系统?')
    start_time = time.perf_counter_ns()  # 开始计时
    main()  # 主函数
    end_time = time.perf_counter_ns()  # 停止计时
    print("运行时间: {:.9f} 秒".format((end_time - start_time) / 1e9))  # 输出用时
