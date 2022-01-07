import cv2
import mediapipe as mp

# Initialize the mediapipe hands class.
mp_hands = mp.solutions.hands

# Set up the Hands functions for images and videos.
hands_videos = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5)


def detectHandsLandmarks(image, hands):
    """
    This function performs hands landmarks detection on an image.

    :param image:   The input image with prominent hand(s) whose landmarks needs to be detected.
    :param hands:   The Hands function required to perform the hands landmarks detection.
    :returns:
        - **output_image** - A copy of input image with the detected hands landmarks drawn if it was specified.
        - **results** - The output of the hands landmarks detection on the input image.
    """

    # Create a copy of the input image to draw landmarks on.
    output_image = image.copy()

    '''
    # Convert the image from BGR into RGB format.
    imgRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    '''
    # Perform the Hands Landmarks Detection.
    results = hands.process(image)

    # Return the output image and results of hands landmarks detection.
    return output_image, results


def countFingers(image, results):
    """
    This function will count the number of fingers up for each hand in the image.

    :param image:   The image of the hands on which the fingers counting is required to be performed.
    :param results: The output of the hands landmarks detection performed on the image of the hands.
    :returns:
        - **output_image** - A copy of the input image with the fingers count written, if it was specified.
        - **fingers_statuses** - A dictionary containing the status (i.e., open or close) of each finger of both hands.
        - **count** - A dictionary containing the count of the fingers that are up, of both hands.
    """

    # Get the height and width of the input image.
    height, width, _ = image.shape

    # Create a copy of the input image to write the count of fingers on.
    output_image = image.copy()

    # Initialize a dictionary to store the count of fingers of both hands.
    count = {'RIGHT': 0, 'LEFT': 0}

    # Store the indexes of the tips landmarks of each finger of a hand in a list.
    fingers_tips_ids = [mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                        mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.PINKY_TIP]

    # Initialize a dictionary to store the status (i.e., True for open and False for close) of each finger of both hands.
    fingers_statuses = {'RIGHT_THUMB': False, 'RIGHT_INDEX': False, 'RIGHT_MIDDLE': False, 'RIGHT_RING': False,
                        'RIGHT_PINKY': False, 'LEFT_THUMB': False, 'LEFT_INDEX': False, 'LEFT_MIDDLE': False,
                        'LEFT_RING': False, 'LEFT_PINKY': False}

    # Iterate over the found hands in the image.
    for hand_index, hand_info in enumerate(results.multi_handedness):

        # Retrieve the label of the found hand.
        hand_label = hand_info.classification[0].label

        # Retrieve the landmarks of the found hand.
        hand_landmarks = results.multi_hand_landmarks[hand_index]

        # Iterate over the indexes of the tips landmarks of each finger of the hand.
        for tip_index in fingers_tips_ids:

            # Retrieve the label (i.e., index, middle, etc.) of the finger on which we are iterating upon.
            finger_name = tip_index.name.split("_")[0]

            if (hand_landmarks.landmark[0].y > hand_landmarks.landmark[tip_index].y):
                # Hand up
                # Check if the finger is up by comparing the y-coordinates of the tip and pip landmarks.
                if (hand_landmarks.landmark[tip_index].y < hand_landmarks.landmark[tip_index - 2].y):
                    # Update the status of the finger in the dictionary to true.
                    fingers_statuses[hand_label.upper() + "_" + finger_name] = True

                    # Increment the count of the fingers up of the hand by 1.
                    count[hand_label.upper()] += 1
            else:
                # Hand down
                # Check if the finger is up by comparing the y-coordinates of the tip and pip landmarks.
                if (hand_landmarks.landmark[tip_index].y > hand_landmarks.landmark[tip_index - 2].y):
                    # Update the status of the finger in the dictionary to true.
                    fingers_statuses[hand_label.upper() + "_" + finger_name] = True

                    # Increment the count of the fingers up of the hand by 1.
                    count[hand_label.upper()] += 1

        # Retrieve the x-coordinates of the tip and mcp landmarks of the thumb of the hand.
        thumb_tip_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x
        thumb_mcp_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP - 2].x

        # Check if the thumb is up by comparing the hand label and the x-coordinates of the retrieved landmarks.
        if (hand_label == 'Right' and (thumb_tip_x < thumb_mcp_x)) or (
                hand_label == 'Left' and (thumb_tip_x > thumb_mcp_x)):
            # Update the status of the thumb in the dictionary to true.
            fingers_statuses[hand_label.upper() + "_THUMB"] = True

            # Increment the count of the fingers up of the hand by 1.
            count[hand_label.upper()] += 1

    # Return the output image, the status of each finger and the count of the fingers up of both hands.
    return output_image, fingers_statuses, count