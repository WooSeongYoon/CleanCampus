import matplotlib.pyplot as plt
import cv2
from inference_sdk import InferenceHTTPClient

def prc(img_path):
    CLIENT = InferenceHTTPClient(
        api_url="https://detect.roboflow.com",
        api_key="EJA9JwWYfAVqqZ3kLOhz"
    )

    # 탐지된 이미지 저장
    result = CLIENT.infer(img_path, model_id="garbage-detection-sht1u/4")

    textList = []

    if 'predictions' in result:
        for prediction in result['predictions']:
            textList.append([prediction['class'], round(prediction['confidence'], 2) * 100])

    if not textList:
        return "Fail, 0"

    else:
        probability = 0
        text = ""

        for a in textList:
            text += a[0] + " "
            probability += a[1]

        average_probability = probability / len(textList)

        # 이미지 출력
        img = cv2.imread(img_path)
        
        for prediction in result['predictions']:
            # 바운딩 박스 좌표 수정
            x_center = int(prediction['x'])  # 중심 x
            y_center = int(prediction['y'])  # 중심 y
            width = int(prediction['width'])  # 너비
            height = int(prediction['height'])  # 높이
            
            # 좌측 상단과 우측 하단 좌표 계산
            x1 = x_center - (width // 2)  # 좌측 상단 x
            y1 = y_center - (height // 2)  # 좌측 상단 y
            x2 = x_center + (width // 2)  # 우측 하단 x
            y2 = y_center + (height // 2)  # 우측 하단 y
            
            print("bounding box 좌표:", x1, y1, x2, y2)

            label = prediction['class']
            confidence = round(prediction['confidence'], 2) * 100

            # 이미지에 bounding box 그리기
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(img, f"{label}: {confidence:.2f}%", (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

            # 이미지 저장
            cv2.imwrite(img_path, img)

        # # 이미지 출력
        # plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        # plt.axis('off')
        # plt.show()

        return f"Success, {average_probability:.2f}, {text}"

# 사용 예시
if __name__ == "__main__":
    print("1")
    print(prc('aiTest/t.jpg'))
