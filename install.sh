python -mpip install -U pip setuptools
pip install "paddleocr==2.6.1.1"
python3 -m pip install paddlepaddle-gpu==2.4.1.post112 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html
# conda install paddlepaddle-gpu==2.4.1 cudatoolkit=11.2 -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/Paddle/ -c conda-forge -y
# sudo apt-get install libgl1 -y
# pip uninstall numpy -y
pip install "numpy==1.21.6"
pip install 'protobuf~=3.19.0'
pip install gpustat

python demo.py