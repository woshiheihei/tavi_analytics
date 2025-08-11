import requests
import time
import os


#命令行命令：
"""
curl -X POST -F "file=@./data/dianxing/dcm/ori_raw.nrrd" http://192.168.4.210:5000/upload 上传
curl -X GET http://192.168.4.210:5000/status/{task-id}  查询状态
curl -X GET http://http://192.168.4.210:5000/result/segmentation/{task-id} -o segment_result.nrrd 获取分割文件
curl -X GET http://http://192.168.4.210:5000/result/measurement/{task-id} -o measurement.json  获取测量结果
"""




class DCMProcessor:
    def __init__(self, base_url="http://192.168.4.210:5000"):
        self.base_url = base_url

    def upload_file(self, file_path):
        """
        上传文件到服务器

        Args:
            file_path (str): 本地文件路径

        Returns:
            str: 任务ID
        """
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{self.base_url}/upload", files=files)

        if response.status_code == 200:
            task_id = response.json().get('task_id')
            print(f"文件上传成功，任务ID: {task_id}")
            return task_id
        else:
            raise Exception(f"文件上传失败: {response.status_code} - {response.text}")

    def check_status(self, task_id):
        """
        查询任务状态

        Args:
            task_id (str): 任务ID

        Returns:
            str: 任务状态
        """
        response = requests.get(f"{self.base_url}/status/{task_id}")

        if response.status_code == 200:
            status = response.json().get('status')
            print(f"任务 {task_id} 状态: {status}")
            return status
        else:
            raise Exception(f"状态查询失败: {response.status_code} - {response.text}")

    def wait_for_completion(self, task_id, check_interval=5):
        """
        等待任务完成

        Args:
            task_id (str): 任务ID
            check_interval (int): 查询间隔（秒）
        """
        print("等待任务完成...")
        while True:
            status = self.check_status(task_id)
            if status == 'completed':
                print("任务已完成")
                break
            elif status == 'failed':
                raise Exception("任务执行失败")
            time.sleep(check_interval)

    def download_segmentation_result(self, task_id, output_path="segment_result.nrrd"):
        """
        下载分割结果文件

        Args:
            task_id (str): 任务ID
            output_path (str): 输出文件路径
        """
        response = requests.get(f"{self.base_url}/result/segmentation/{task_id}")

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"分割结果已保存至: {output_path}")
        else:
            raise Exception(f"下载分割结果失败: {response.status_code} - {response.text}")

    def download_measurement_result(self, task_id, output_path="measurement.json"):
        """
        下载测量结果文件

        Args:
            task_id (str): 任务ID
            output_path (str): 输出文件路径
        """
        response = requests.get(f"{self.base_url}/result/measurement/{task_id}")

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"测量结果已保存至: {output_path}")
        else:
            raise Exception(f"下载测量结果失败: {response.status_code} - {response.text}")

    def process_file(self, file_path, seg_output="segment_result.nrrd",
                     measure_output="measurement.json"):
        """
        完整处理流程：上传文件 -> 等待完成 -> 下载结果

        Args:
            file_path (str): 输入文件路径
            seg_output (str): 分割结果输出路径
            measure_output (str): 测量结果输出路径
        """
        # 上传文件
        task_id = self.upload_file(file_path)

        # 等待任务完成
        self.wait_for_completion(task_id)

        # 下载结果
        self.download_segmentation_result(task_id, seg_output)
        self.download_measurement_result(task_id, measure_output)

        print("所有处理已完成！")


# 使用示例
if __name__ == "__main__":
    processor = DCMProcessor()

    # 处理指定文件
    input_file = "C:\\code\\python\\slicer\\tavi_analytics\\data\\ori_raw.nrrd"

    if os.path.exists(input_file):
        try:
            processor.process_file(input_file)
        except Exception as e:
            print(f"处理过程中出现错误: {e}")
    else:
        print(f"文件不存在: {input_file}")