def prc(img):
    from inference_sdk import InferenceHTTPClient
    
    CLIENT = InferenceHTTPClient(
        api_url="https://detect.roboflow.com",
        api_key="EJA9JwWYfAVqqZ3kLOhz"
    )
    
    result = CLIENT.infer(img, model_id="ultimate-rqkdd/1")

    textList = []

    if 'predictions' in result:
        for prediction in result['predictions']:
            textList.append([prediction['class'], ((round(prediction['confidence'], 2))*100)])

    if textList == []:
        return "Fail, 0"
    
    else:
        probability = 0
        text = ""

        for a in textList:
            text += a[0] + " "
            probability += int(a[1])
            del a[0]
            del a[0]

        return ("Success," + str(probability/len(textList)) +"," + text)

if __name__ == "__main__":
    print("1")
    print(prc('aiTest/t.jpg'))