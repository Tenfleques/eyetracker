import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt

def geometric_len(contour):
    ''' geometric length of contour'''

    cnt = contour.squeeze()
    length = 0
    for i, point in enumerate(cnt[:-1]):
        length += np.linalg.norm(cnt[i + 1] - cnt[i])
    return length


def external_contours(contours, hierarchy, parent):
    ''' choose longest contour from external'''
    contours_external = []
    for idx, h in enumerate(hierarchy.squeeze()):
        if h[3] == parent:
            contours_external.append(contours[idx])
    return max(contours_external, key=lambda x: geometric_len(x))


def clear_border(img):
    ''' add 3 pixels from each side in order to avoid image border intersection'''
    img_array = np.ones((img.shape[0] + 6, img.shape[1] + 6, img.shape[2])) * 255
    for i in range(3, img.shape[0] + 3):
        for j in range(3, img.shape[1] + 3):
            img_array[i][j] = img[i - 3][j - 3]
    return img_array.astype('uint8')


def close_image(image, quad_erode_iter, rec_erode_iter, dilate_iter):
    ''' close external contour'''

    im = image.copy()

    kernel = np.ones((3, 1), np.uint8)
    res = cv.erode(im.copy(), kernel, iterations=quad_erode_iter)

    kernel = np.ones((1, 3), np.uint8)
    res = cv.erode(res.copy(), kernel, iterations=rec_erode_iter)

    kernel = np.ones((3, 3), np.uint8)
    res = cv.dilate(res.copy(), kernel, iterations=dilate_iter)

    return clear_border(res)


def get_contours(img):
    imgray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, thresh = cv.threshold(imgray, 220, 255, cv.THRESH_TOZERO)
    contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    return contours, hierarchy


def gaussian_smooth(border, sigma=5):
    from scipy import ndimage

    y = border.squeeze()[:, 1]
    x = border.squeeze()[:, 0]

    # convert both to arrays
    x_sm = np.array(x)
    y_sm = np.array(y)

    # gaussian smoothing
    x_g1d = ndimage.gaussian_filter1d(x_sm, sigma)
    y_g1d = ndimage.gaussian_filter1d(y_sm, sigma)

    return x_g1d, y_g1d


def processing_image(img, sigma=5, quad_erode_iter=2, rec_erode_iter=2, dilate_iter=1, rescale=0.5):

    ''' if rescale != 0, then size of image is changed '''
    if rescale:
        width = int(img.shape[1] * rescale)
        height = int(img.shape[0] * rescale)
        dim = (width, height)
        image = cv.resize(img, dim, interpolation=cv.INTER_AREA)

    else:
        image = img

    image = close_image(image, quad_erode_iter, rec_erode_iter, dilate_iter)

    if rescale:
        width = int((1+image.shape[1]) / rescale)
        height = int((1+image.shape[0]) / rescale)
        dim = (width, height)
        image = cv.resize(image.copy(), dim, interpolation=cv.INTER_AREA)

    contours, hierarchy = get_contours(image)
    parent = hierarchy.squeeze()[1][3]

    external_contour = external_contours(contours, hierarchy, parent)

    approx_x, approx_y = gaussian_smooth(external_contour, sigma)

    return approx_x, approx_y


def process_image(img, processing=True, sigma=5, quad_erode_iter=2, rec_erode_iter=2, dilate_iter=1, rescale=0.5):
    if processing:
        approx_x, approx_y = processing_image(img, sigma, quad_erode_iter, rec_erode_iter, dilate_iter, rescale)
        points = []
        for i, (x, y) in enumerate(zip(approx_x[:-1], approx_y[:-1])):
            points.append(((x, y), (approx_x[i + 1], approx_y[i + 1])))

        
            
        background = np.ones((img.shape[0], img.shape[1], img.shape[2])) * 255
    
        for l in points:
            background = cv.line(background, l[0], l[1], (0,0,0), 5)
            
        background = cv.line(background, points[-1][-1], points[0][0], (0,0,0), 5)
        background = cv.circle(background, l[0], 5*2, color = (0,0,255), thickness = 10)

        return (background,points)

    new_img = clear_border(img)

    contours, hierarchy = get_contours(new_img)
    parent = hierarchy.squeeze()[1][3]

    external_contour = external_contours(contours, hierarchy, parent)

    points = []
    for i, (x, y) in enumerate(external_contour.squeeze()[:-1]):
        points.append(((x, y), (external_contour.squeeze()[i + 1][0], external_contour.squeeze()[i + 1][1])))

    background = np.ones((new_img.shape[0], new_img.shape[1], new_img.shape[2])) * 255
    
    for l in points:
        background = cv.line(background, l[0], l[1], (0,0,0), 5)
        
    background = cv.line(background, points[-1][-1], points[0][0], (0,0,0), 5)
    background = cv.circle(background, l[0], 5*2, color = (0,0,255), thickness = 10)

    return (background,points)


