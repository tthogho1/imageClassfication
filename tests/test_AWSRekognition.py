import unittest
from unittest.mock import patch, MagicMock
import os
from src.AWSRekognition import RekognitionImage, convertToJson


class TestRekognitionImage(unittest.TestCase):
    @patch("src.AWSRekognition.boto3.client")
    def test_detect_labels(self, mock_boto_client):
        # モッククライアントとレスポンス
        mock_client = MagicMock()
        mock_response = {
            "Labels": [
                {
                    "Name": "Person",
                    "Confidence": 99.0,
                    "Categories": [{"Name": "People"}],
                },
                {
                    "Name": "Car",
                    "Confidence": 88.5,
                    "Categories": [{"Name": "Vehicle"}],
                },
            ]
        }
        mock_client.detect_labels.return_value = mock_response
        image = {"Bytes": b"dummy"}
        rekognition_image = RekognitionImage(image, "dummy.jpg", mock_client)
        labels = rekognition_image.detect_labels()
        self.assertEqual(len(labels), 2)
        self.assertEqual(labels[0]["Name"], "Person")
        self.assertEqual(labels[1]["Name"], "Car")

    def test_convertToJson(self):
        fileid = "test.jpg"
        rekognition_outputs = [
            {"Name": "Person", "Confidence": 99.0, "Categories": [{"Name": "People"}]},
            {"Name": "Car", "Confidence": 88.5, "Categories": [{"Name": "Vehicle"}]},
        ]
        result = convertToJson(fileid, rekognition_outputs)
        self.assertEqual(result["image_id"], fileid)
        self.assertIn("People", result["categories"])
        self.assertIn("Vehicle", result["categories"])
        self.assertEqual(len(result["tags"]), 2)
        self.assertEqual(result["tags"][0]["name"], "Person")
        self.assertEqual(result["tags"][1]["name"], "Car")


if __name__ == "__main__":
    unittest.main()
