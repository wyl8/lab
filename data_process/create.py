from example_dataset_dataset_builder import *
import pdb
# 创建数据集构建器实例
dataset_builder = ExampleDataset()
pdb.set_trace()
# 打印数据集信息以验证配置
print(dataset_builder.info)

# 生成数据集拆分
splits = dataset_builder._split_generators(dl_manager=None)

# 生成训练数据样本并进行迭代
for example in dataset_builder._generate_examples(splits['train']):
    # 处理或查看样本，例如打印或保存
    print(example)

# 生成验证数据样本并进行迭代
for example in dataset_builder._generate_examples(splits['val']):
    # 处理或查看样本，例如打印或保存
    print(example)