import json

class GroupmeMessage:

  def __init__(self, lambda_event):
    self.request = json.loads(lambda_event["body"])
    print("GroupMe Message Received: " + json.dumps(self.request))

  def is_bot_post(self):
    return self.request['sender_type'] != 'user'

  def is_image_post(self):
    return self.__has_native_image() or self.__has_linked_image()

  def get_image_url(self):
    if self.__has_native_image():
      return self.request["attachments"][0]["url"]
    elif self.__has_linked_image():
      return self.request["text"]
    else:
      raise ValueError("attempted to get image url from a non-image message")

  def __has_native_image(self):
    # For when the image is uploaded to groupme api
    if (not "attachments" in self.request):
        return False

    attachments = self.request["attachments"]

    if (len(attachments) != 1):
        return False

    attachment = attachments[0]

    return "type" in attachment and attachment["type"] == 'image'

  def __has_linked_image(self):
    # For when image was linked in the message text (e.g. to imgur)
    if (not "attachments" in self.request):
        return False

    attachments = self.request["attachments"]

    if (len(attachments) != 1):
        return False

    attachment = attachments[0]

    return (
        "type" in attachment and attachment["type"] == "postprocessing"
        and "queues" in attachment and attachment["queues"][0] == "linked_image"
    )