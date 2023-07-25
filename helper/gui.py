import pyautogui as ag


def getElementBounds(box):
    bounds = None
    if box is not None:
        left, top, width, height = box.left, box.top, box.width, box.height
        bounds = (left, top, width, height)
    return bounds


def getCenter(bounds):
    left, top, width, height = bounds
    x, y = left + width // 2, top + height // 2
    return x, y


def getElementCenter(element):
    bounds = getElementBounds(element)
    x, y = getCenter(bounds)
    return x, y


def typeWaitElement(image, text, bounds, searchTime: int = 60):
    element = ag.locateOnScreen(image, region=bounds, minSearchTime=searchTime)
    if element is not None:
        ag.typewrite(text)
        x, y = getElementCenter(element)
        ag.click(x, y)
