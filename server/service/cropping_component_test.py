import unittest
import cv2
from app.components.cropping_component import Cropping

class CroppingTestCase(unittest.TestCase):
    def setUp(self):
        # Set up any necessary objects or data for the tests
        params = {
            'filling': 10,
            'crop_margin': 1.3,
            'crop_size_width': 120,
            'cascade': 'haarcascade_frontalface_default.xml'
        }
        self.cropping = Cropping()
        self.cropping.init(params)

    def tearDown(self):
        # Clean up any resources used by the tests
        pass

    def test_cropping_with_no_faces(self):
        # Test case for when no faces are detected
        image = cv2.imread('./test/no_faces.png')  # Provide a test image with no faces
        cropped, messages = self.cropping.cropping(image)
        self.assertEqual(len(cropped), 0)
        self.assertEqual(len(messages), 0)

    def test_cropping_with_one_face(self):
        # Test case for when one face is detected
        image = cv2.imread('./test/one_face.jpg')  # Provide a test image with a single face
        cropped, messages = self.cropping.cropping(image)
        self.assertEqual(cropped.shape, (120, 120, 3))  # Adjust the expected shape based on the crop size
        self.assertEqual(len(messages), 0)

    def test_cropping_with_multiple_faces(self):
        # Test case for when multiple faces are detected
        image = cv2.imread('./test/multiple_faces.png')  # Provide a test image with multiple faces
        cropped, messages = self.cropping.cropping(image)
        self.assertEqual(len(cropped), 0)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], 'only_one_face')

    def test_cropping_with_insufficient_filling(self):
        # Test case for when the cropping does not meet the desired filling percentage
        image = cv2.imread('./test/insufficient_filling.jpg')  # Provide a test image with a single face
        # Adjust the filling value in the parameters to a value that will fail the condition
        cropped, messages = self.cropping.cropping(image)
        self.assertEqual(len(cropped), 0)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], 'come_closer')

    def test_cropping_with_too_close_face(self):
        # Test case for when the face is too close to the frame boundary
        image = cv2.imread('./test/too_close_face.jpg')  # Provide a test image with a single face
        cropped, messages = self.cropping.cropping(image)
        self.assertEqual(len(cropped), 0)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], 'too_close')

if __name__ == '__main__':
    unittest.main()
