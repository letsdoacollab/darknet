import os
import cv2
import time
import darknet
import argparse
import random


def parser():
    parser = argparse.ArgumentParser(description="YOLO Object Detection")
    parser.add_argument("--input", type=str, default=0,
                        help="video source. If empty, uses webcam 0 stream")
    parser.add_argument("--output_file", type=str, default="",
                        help="inference video name. Not saved if empty")
    parser.add_argument("--weights", default="yolov4.weights",
                        help="yolo weights path")
    parser.add_argument("--dont_show", action='store_true',
                        help="windown inference display. For headless systems")
    parser.add_argument("--ext_output", action='store_true',
                        help="display bbox coordinates of detected objects")
    parser.add_argument("--config_file", default="./cfg/yolov4.cfg",
                        help="path to config file")
    parser.add_argument("--data_file", default="./cfg/coco.data",
                        help="path to data file")
    parser.add_argument("--thresh", type=float, default=.25,
                        help="remove detections with confidence below this value")
    return parser.parse_args()


def check_arguments_errors(args):
    assert 0 < args.thresh < 1, "Threshold should be a float between zero and one (non-inclusive)"
    if not os.path.exists(args.config_file):
        raise(ValueError("Invalid config path {}".format(os.path.abspath(args.config_file))))
    if not os.path.exists(args.weights):
        raise(ValueError("Invalid weight path {}".format(os.path.abspath(args.weights))))
    if not os.path.exists(args.data_file):
        raise(ValueError("Invalid data file path {}".format(os.path.abspath(args.data_file))))
    if args.input and not os.path.exists(args.input):
        raise(ValueError("Invalid image path {}".format(os.path.abspath(args.input))))


def set_video(input_video, output_video, size, fps=15):
    """
    Setup input and ouput (saved) video objects
        args:
            input_video (str): path to video, or webcam device number
            output_video (str): inference video name to be saved
            fps: frames per second for saved video (adjust this number for
            player speed)
        returns:
            cap: cv2 input video object
            video: cv2 output video object
    """
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    video = cv2.VideoWriter(output_video, fourcc, fps, size)
    return video


def main():
    args = parser()
    check_arguments_errors(args)
    random.seed(3)  # deterministic bbox colors

    network, class_names, class_colors = darknet.load_network(
        args.config_file,
        args.data_file,
        args.weights
    )
    # Darknet doesn't accept numpy images.
    # Create one with image we reuse for each detect
    width = darknet.network_width(network)
    height = darknet.network_height(network)
    darknet_image = darknet.make_image(width, height, 3)

    cap = cv2.VideoCapture(args.input)
    video = set_video(args.input, args.output_file, (width, height))

    while cap.isOpened():
        prev_time = time.time()
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (width, height),
                                   interpolation=cv2.INTER_LINEAR)
        darknet.copy_image_from_bytes(darknet_image, frame_resized.tobytes())
        detections = darknet.detect_image(network, class_names, darknet_image, thresh=args.thresh)
        image = darknet.draw_boxes(detections, frame_resized, class_colors)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        if args.output_file is not None:
            video.write(image)
        fps = int(1/(time.time() - prev_time))
        print("FPS: {}".format(fps))
        darknet.print_detections(detections, args.ext_output)
        if not args.dont_show:
            cv2.imshow('Inference', image)
            cv2.waitKey(fps)
    cap.release()
    video.release()


if __name__ == "__main__":
    main()
