import pickle
import re
import wx
import wx.lib.buttons as buttons

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# DragList


class DragList(wx.ListCtrl):
    def __init__(self, *arg, **kw):
        wx.ListCtrl.__init__(self, *arg, **kw)

        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._startDrag)

        dt = ListDrop(self)
        self.SetDropTarget(dt)

        # for the images
        isz = (16, 16)
        self.il = wx.ImageList(isz[0], isz[1])
        self.fldridx = self.il.Add(
            wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz)
        )
        self.fldropenidx = self.il.Add(
            wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, isz)
        )
        self.fileidx = self.il.Add(
            wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz)
        )

        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        info = wx.ListItem()
        info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
        info.m_image = -1
        info.m_format = 0
        info.m_text = ""
        self.InsertColumnInfo(0, info)

        # self.il = il

    def getItemInfo(self, idx):
        """Collect all relevant data of a listitem, and put it in a list"""
        l = []
        l.append(
            idx
        )  # We need the original index, so it is easier to eventualy delete it
        l.append(self.GetItemData(idx))  # Itemdata
        l.append(self.GetItemText(idx))  # Text first column
        for i in range(1, self.GetColumnCount()):  # Possible extra columns
            l.append(self.GetItem(idx, i).GetText())
        return l

    def _startDrag(self, e):
        """ Put together a data object for drag-and-drop _from_ this list. """
        l = []
        idx = -1
        while True:  # find all the selected items and put them in a list
            idx = self.GetNextItem(idx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if idx == -1:
                break
            l.append(self.getItemInfo(idx))

        # Pickle the items list.
        itemdata = pickle.dumps(l, 1)
        # create our own data format and use it in a
        # custom data object
        ldata = wx.CustomDataObject("ListCtrlItems")
        ldata.SetData(itemdata)
        # Now make a data object for the  item list.
        data = wx.DataObjectComposite()
        data.Add(ldata)

        # Create drop source and begin drag-and-drop.
        dropSource = wx.DropSource(self)
        dropSource.SetData(data)
        res = dropSource.DoDragDrop(flags=wx.Drag_DefaultMove)

        # If move, we want to remove the item from this list.
        if res == wx.DragMove:
            # It's possible we are dragging/dropping from this list to this list.  In which case, the
            # index we are removing may have changed...

            # Find correct position.
            l.reverse()  # Delete all the items, starting with the last item
            for i in l:
                pos = self.FindItem(i[0], i[2])
                self.DeleteItem(pos)

    def _insert(self, x, y, seq):
        """ Insert text at given x, y coordinates --- used with drag-and-drop. """

        # Find insertion point.
        index, flags = self.HitTest((x, y))

        if index == wx.NOT_FOUND:  # not clicked on an item
            if flags & (
                wx.LIST_HITTEST_NOWHERE | wx.LIST_HITTEST_ABOVE | wx.LIST_HITTEST_BELOW
            ):  # empty list or below last item
                index = self.GetItemCount()  # append to end of list
            elif self.GetItemCount() > 0:
                if y <= self.GetItemRect(0).y:  # clicked just above first item
                    index = 0  # append to top of list
                else:
                    index = self.GetItemCount() + 1  # append to end of list
        else:  # clicked on an item
            # Get bounding rectangle for the item the user is dropping over.
            rect = self.GetItemRect(index)

            # If the user is dropping into the lower half of the rect, we want to insert _after_ this item.
            # Correct for the fact that there may be a heading involved
            # if y > rect.y - self.GetItemRect(0).y + rect.height/2:
            index += 1

        if not isinstance(seq, list):
            idx = self.InsertImageStringItem(index, seq, self.fileidx)
        else:
            for i in seq:  # insert the item data
                # idx = self.InsertStringItem(index, i[2])
                idx = self.InsertImageStringItem(index, i[2], self.fileidx)
                # self.SetItemData(idx, i)
                for j in range(1, self.GetColumnCount()):
                    try:  # Target list can have more columns than source
                        # self.SetStringItem(idx, j, i[2+j])
                        idx = self.InsertImageStringItem(idx, j, self.fileidx)
                    except:
                        pass  # ignore the extra columns
                index += 1


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ListDrop


class ListDrop(wx.PyDropTarget):
    """ Drop target for simple lists. """

    def __init__(self, source):
        """ Arguments:
		 - source: source listctrl.
		"""
        wx.PyDropTarget.__init__(self)

        self.dv = source

        # specify the type of data we will accept
        self.data = wx.CustomDataObject("ListCtrlItems")
        self.SetDataObject(self.data)

    # Called when OnDrop returns True.  We need to get the data and
    # do something with it.
    def OnData(self, x, y, d):

        # copy the data from the drag source to our data object
        if self.GetData():
            # convert it back to a list and give it to the viewer
            ldata = self.data.GetData()
            l = pickle.loads(ldata)
            self.dv._insert(x, y, l)

        # what is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return d

    ################
    ### DragTree ###
    ################


class DragTree(wx.TreeCtrl):
    def __init__(self, *arg, **kw):
        wx.TreeCtrl.__init__(self, *arg, **kw)

        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self._startDrag)

        self.parent = arg[0]

        dt = TreeDrop(self)
        self.SetDropTarget(dt)

        # for the images
        isz = (16, 16)
        il = wx.ImageList(isz[0], isz[1])
        self.fldridx = il.Add(
            wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz)
        )
        self.fldropenidx = il.Add(
            wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, isz)
        )
        self.fileidx = il.Add(
            wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz)
        )

        self.SetImageList(il)
        self.il = il

        self.treeroot = self.AddRoot("Groups")
        self.SetItemImage(self.treeroot, self.fldridx, wx.TreeItemIcon_Normal)
        self.SetItemImage(self.treeroot, self.fldropenidx, wx.TreeItemIcon_Expanded)

    def getItemInfo(self, idx):
        """Collect all relevant data of a listitem, and put it in a list"""
        l = []
        l.append(
            idx
        )  # We need the original index, so it is easier to eventualy delete it
        l.append(self.GetItemData(idx))  # Itemdata
        l.append(self.GetItemText(idx))  # Text first column
        for i in range(1, self.GetColumnCount()):  # Possible extra columns
            l.append(self.GetItem(idx, i).GetText())
        return l

    def _startDrag(self, e):
        """ Put together a data object for drag-and-drop _from_ this list. """

        selectedGroups = self.GetSelections()
        for item in selectedGroups:

            label = self.GetItemText(item)
            m = re.compile("^Group_[0-9]+")

            if m.match(label):

                treeItems = []
                groupItems = []

                first, cookie = self.GetFirstChild(item)

                if first.IsOk():  # are there children?
                    treeItems.append((first, self.GetItemText(first)))
                    i, cookie = self.GetNextChild(first, cookie)

                    while i.IsOk():
                        treeItems.append((i, self.GetItemText(i)))
                        i, cookie = self.GetNextChild(i, cookie)

                    for i in treeItems:
                        # self.dragList_left.InsertStringItem(self.dragList_left.GetItemCount(), i[1])
                        # self.Delete(i[0])

                        ## Create drop source and begin drag-and-drop.
                        itemdata = pickle.dumps(i[1], 1)
                        ldata = wx.CustomDataObject("ListCtrlItems")
                        ldata.SetData(itemdata)
                        data = wx.DataObjectComposite()
                        data.Add(ldata)
                        dropSource = wx.DropSource(self)
                        dropSource.SetData(data)
                        res = dropSource.DoDragDrop(flags=wx.Drag_DefaultMove)

                        # If move, we want to remove the item from this list.
                        if res == wx.DragMove:
                            # It's possible we are dragging/dropping from this list to this list.  In which case, the
                            # index we are removing may have changed...

                            # Find correct position.
                            # l.reverse() # Delete all the items, starting with the last item
                            # for i in l:
                            # 	pos = self.FindItem(i[0], i[2])
                            # 	self.DeleteItem(pos)
                            self.Delete(i[0])

                self.Delete(item)

            else:

                i = self.GetItemText(item)
                # treeItems = []
                # groupItems = []

                # first, cookie = self.GetFirstChild(item)
                # treeItems.append((first, self.GetItemText(first)))
                # i, cookie = self.GetNextChild(first, cookie)

                # while i.IsOk():
                # 	treeItems.append((i, self.GetItemText(i)))
                # 	i, cookie = self.GetNextChild(i, cookie)

                # for i in treeItems:
                ## Pickle the items list.
                ## create our own data format and use it in a
                ## custom data object
                ## Now make a data object for the  item list.

                # Create drop source and begin drag-and-drop.
                itemdata = pickle.dumps(i, 1)
                ldata = wx.CustomDataObject("ListCtrlItems")
                ldata.SetData(itemdata)
                data = wx.DataObjectComposite()
                data.Add(ldata)
                dropSource = wx.DropSource(self)
                dropSource.SetData(data)
                res = dropSource.DoDragDrop(flags=wx.Drag_DefaultMove)

                # If move, we want to remove the item from this list.
                if res == wx.DragMove:
                    # It's possible we are dragging/dropping from this list to this list.  In which case, the
                    # index we are removing may have changed...

                    # Find correct position.
                    # l.reverse() # Delete all the items, starting with the last item
                    # for i in l:
                    # 	pos = self.FindItem(i[0], i[2])
                    # 	self.DeleteItem(pos)
                    self.Delete(item)

    def _insert(self, x, y, seq):
        """ Insert text at given x, y coordinates --- used with drag-and-drop. """

        # Find insertion point.
        index, flags = self.HitTest((x, y))
        m = re.compile("^Group_[0-9]+")

        # if index == wx.NOT_FOUND: # not clicked on an item
        # 	if flags & (wx.LIST_HITTEST_NOWHERE|wx.LIST_HITTEST_ABOVE|wx.LIST_HITTEST_BELOW): # empty list or below last item
        # 		index = self.GetItemCount() # append to end of list
        # 	elif self.GetItemCount() > 0:
        # 		if y <= self.GetItemRect(0).y: # clicked just above first item
        # 			index = 0 # append to top of list
        # 		else:
        # 			index = self.GetItemCount() + 1 # append to end of list
        # else: # clicked on an item
        # 	# Get bounding rectangle for the item the user is dropping over.
        # 	rect = self.GetItemRect(index)

        # 	# If the user is dropping into the lower half of the rect, we want to insert _after_ this item.
        # 	# Correct for the fact that there may be a heading involved
        # 	if y > rect.y - self.GetItemRect(0).y + rect.height/2:
        # 		index += 1

        if isinstance(seq, list):  # comes from the left listctrl

            if not index.IsOk():  # index has no dropping goal

                g = self.parent.OnAddGroup(None)
                self.Expand(g)

            else:  # not self.GetItemText(index) == 'Groups':

                if m.match(self.GetItemText(index)):

                    for i in seq:  # insert the item data
                        idx = self.AppendItem(index, i[2])
                        self.SetItemImage(idx, self.fileidx, wx.TreeItemIcon_Normal)
                    self.Expand(index)

                else:
                    pass  # do nothing

        else:  # comes from the right treectrl

            if not index.IsOk():

                g = self.parent.OnAddGroup(None)
                if g:
                    self.Expand(g)

            elif m.match(self.GetItemText(index)):

                idx = self.AppendItem(index, seq)
                self.SetItemImage(idx, self.fileidx, wx.TreeItemIcon_Normal)
                self.Expand(index)

            else:
                pass

                # self.SetItemData(idx, i[1])
                # self.SetItemData(idx, i[1])
                # for j in range(1, self.GetColumnCount()):
                # 	try: # Target list can have more columns than source
                # 		self.SetStringItem(idx, j, i[2+j])
                # 	except:
                # 		pass # ignore the extra columns
                # index += 1

    def AddGroup(self, label, items):

        r = self.GetRootItem()
        g = self.AppendItem(r, label)
        self.SetItemImage(g, self.fldridx, wx.TreeItemIcon_Normal)

        for i in items:
            idx = self.AppendItem(g, i)
            self.SetItemImage(idx, self.fileidx, wx.TreeItemIcon_Normal)

        self.Expand(g)

        return g


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# TreeDrop


class TreeDrop(wx.PyDropTarget):
    """ Drop target for simple lists. """

    def __init__(self, source):
        """ Arguments:
		 - source: source listctrl.
		"""
        wx.PyDropTarget.__init__(self)

        self.dv = source

        # specify the type of data we will accept
        self.data = wx.CustomDataObject("ListCtrlItems")
        self.SetDataObject(self.data)

    # Called when OnDrop returns True.  We need to get the data and
    # do something with it.
    def OnData(self, x, y, d):

        # Find insertion point.
        index, flags = self.dv.HitTest((x, y))
        m = re.compile("^Group_[0-9]+")
        if index.IsOk():  # index has no dropping goal
            if not m.match(self.dv.GetItemText(index)):
                return False
            if self.dv.GetRootItem() == index:
                return False

        # copy the data from the drag source to our data object
        if self.GetData():
            # convert it back to a list and give it to the viewer
            ldata = self.data.GetData()
            l = pickle.loads(ldata)
            self.dv._insert(x, y, l)

        # what is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return d


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# main


class ChooseGroupsFrame(wx.Dialog):
    def __init__(self, *args, **kwds1):

        kwds = {}
        kwds["title"] = kwds1["title"]

        # begin wxGlade: LpdxFrame.__init__
        kwds["style"] = (
            wx.MINIMIZE_BOX
            | wx.MAXIMIZE_BOX
            | wx.SYSTEM_MENU
            | wx.CAPTION
            | wx.CLOSE_BOX
            | wx.CLIP_CHILDREN
            | wx.RESIZE_BORDER
        )

        wx.Dialog.__init__(self, *args, **kwds)
        # panel = wx.Panel(self, -1)

        self.font_labels = wx.Font(
            10, wx.SWISS, wx.NORMAL, wx.NORMAL, False
        )  # , 0, 0, wx.FONTENCODING_SYSTEM))
        self.font_ctrl = wx.Font(
            9, wx.SWISS, wx.NORMAL, wx.NORMAL, False
        )  # , 0, 0, wx.FONTENCODING_SYSTEM))
        self.SetFont(self.font_labels)

        self.parent = args[0]
        self.columnsChoosen = []
        self.items = kwds1["items"]

        self.groupCount = 0
        self.groups = []
        self.groupStr = ""

        self.sizer_v = wx.BoxSizer(wx.VERTICAL)
        self.sizer_h = wx.BoxSizer(wx.HORIZONTAL)

        self.label_left = wx.StaticText(
            self,
            -1,
            "Select one or more samples and press \n'Add to group' to form a new group.",
        )

        self.dragList_left = DragList(self, style=wx.LC_LIST, size=(300, 200))
        self.dragList_left.InsertColumn(0, "")
        self.dragList_left.SetFont(self.font_ctrl)

        # for i in self.columnsToChoose:
        # 	self.listBox_left.InsertStringItem(1, i)

        self.button_addGroup = buttons.GenButton(self, -1, "-> Add to a group ->")
        self.button_removeGroup = buttons.GenButton(self, -1, "<- Remove <-")
        self.button_addGroup.SetBackgroundColour(wx.Colour(200, 200, 200))
        self.button_removeGroup.SetBackgroundColour(wx.Colour(200, 200, 200))
        self.label_right = wx.StaticText(self, -1, "Groups are listed here.\n")

        self.dragList_right = DragTree(
            self,
            style=wx.TR_HAS_BUTTONS
            | wx.TR_HIDE_ROOT
            | wx.TR_MULTIPLE
            | wx.TR_DEFAULT_STYLE,
            size=(300, 200),
        )
        self.dragList_right.SetFont(self.font_ctrl)

        self.button_ready = buttons.GenButton(self, -1, "OK")
        self.button_ready.SetBackgroundColour(wx.Colour(200, 200, 200))

        # self.sizer_buttons = wx.BoxSizer(wx.VERTICAL)
        # self.sizer_buttons.Add(self.button_addGroup, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        # self.sizer_buttons.Add(self.button_removeGroup, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.Bind(wx.EVT_BUTTON, self.OnAddGroup, self.button_addGroup)
        self.Bind(wx.EVT_BUTTON, self.OnRemoveGroup, self.button_removeGroup)
        self.Bind(wx.EVT_BUTTON, self.OnOK, self.button_ready)

        self.sizer_leftPart = wx.BoxSizer(wx.VERTICAL)
        self.sizer_leftPart.Add(self.label_left, 0, wx.ALIGN_LEFT | wx.ALL, 4)
        self.sizer_leftPart.Add(self.dragList_left, 0, wx.ALIGN_LEFT | wx.ALL, 4)
        self.sizer_leftPart.Add(self.button_addGroup, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.sizer_rightPart = wx.BoxSizer(wx.VERTICAL)
        self.sizer_rightPart.Add(self.label_right, 0, wx.ALIGN_LEFT | wx.ALL, 4)
        self.sizer_rightPart.Add(self.dragList_right, 0, wx.ALIGN_LEFT | wx.ALL, 4)
        self.sizer_rightPart.Add(
            self.button_removeGroup, 0, wx.ALIGN_CENTER | wx.ALL, 5
        )

        self.sizer_h.Add(self.sizer_leftPart, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        # self.sizer_h.Add(self.sizer_buttons, 0, wx.ALIGN_CENTER_VERTICAL)
        self.sizer_h.Add(self.sizer_rightPart, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.sizer_v.Add(self.sizer_h)
        self.sizer_v.Add(self.button_ready, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.SetSizer(self.sizer_v)

        from random import choice
        from sys import maxsize

        for item in self.items:
            # self.dragList_left.InsertStringItem(maxint, item)
            self.dragList_left.InsertStringItem(
                maxint, item, self.dragList_left.fileidx
            )

        self.SetSize((680, 390))
        self.Layout()

    def traverse(self, parent=None):

        if parent is None:
            parent = self.treeroot
        nc = self.dragList_right.GetChildrenCount(parent, False)

        def GetFirstChild(parent, cookie):
            return self.dragList_right.GetFirstChild(parent)

        GetChild = GetFirstChild
        cookie = 1
        for i in range(nc):
            child, cookie = GetChild(parent, cookie)
            GetChild = self.dragList_right.GetNextChild
            yield child

    def OnAddGroup(self, evt, item=None):

        i1 = self.dragList_left.GetFirstSelected()

        if i1 >= 0:

            items = []
            itemsToGroup = []
            while i1 >= 0:
                items.append(i1)
                itemsToGroup.append(self.dragList_left.GetItemText(i1))
                i1 = self.dragList_left.GetNextSelected(i1)

            items.reverse()

            for item in items:
                self.dragList_left.DeleteItem(item)

            self.groupCount += 1
            g = self.dragList_right.AddGroup("Group_%d" % self.groupCount, itemsToGroup)

        elif self.dragList_right.GetSelections() != []:

            i1 = self.dragList_right.GetSelections()

            items = []
            itemsToGroup = []
            for item in i1:
                # while i1 >= 0:
                items.append(item)
                itemsToGroup.append(self.dragList_right.GetItemText(item))

            items.reverse()

            for item in items:
                self.dragList_right.Delete(item)

            self.groupCount += 1
            g = self.dragList_right.AddGroup("Group_%d" % self.groupCount, itemsToGroup)

        return g

    def OnRemoveGroup(self, evt):

        m = re.compile("^Group_[0-9]+")
        selectedGroups = self.dragList_right.GetSelections()

        for item in selectedGroups:

            if m.match(self.dragList_right.GetItemText(item)):

                treeItems = []
                groupItems = []

                first, cookie = self.dragList_right.GetFirstChild(item)

                if first.IsOk():  # are there childrens?
                    treeItems.append((first, self.dragList_right.GetItemText(first)))
                    i, cookie = self.dragList_right.GetNextChild(first, cookie)

                    while i.IsOk():
                        treeItems.append((i, self.dragList_right.GetItemText(i)))
                        i, cookie = self.dragList_right.GetNextChild(i, cookie)

                    for i in treeItems:
                        # self.dragList_left.InsertStringItem(self.dragList_left.GetItemCount(), i[1])
                        self.dragList_left.InsertImageStringItem(
                            self.dragList_left.GetItemCount(),
                            i[1],
                            self.dragList_left.fileidx,
                        )
                        self.dragList_right.Delete(i[0])

                self.dragList_right.Delete(item)

            else:
                self.dragList_left.InsertImageStringItem(
                    self.dragList_left.GetItemCount(),
                    self.dragList_right.GetItemText(item),
                    self.dragList_left.fileidx,
                )
                self.dragList_right.Delete(item)

    def OnOK(self, evt):

        # empty the group variable
        self.groups = []

        # traverse the right tree and collect the entries as
        # a list of lists
        for i in self.traverse(self.dragList_right.GetRootItem()):
            self.groups.append([])
            for j in self.traverse(i):
                self.groups[-1].append(self.dragList_right.GetItemText(j))

        # append the elements of the left window (the source) as
        # a group to self.groups
        if self.dragList_left.GetItemCount() > 0:
            self.groups.append([])
            while self.dragList_left.GetItemCount() > 0:
                self.groups[-1].append(self.dragList_left.GetItemText(0))
                self.dragList_left.DeleteItem(0)

        self.groupStr = self.exportGroups()

        self.Destroy()

    def exportGroups(self):

        if self.groups != []:
            str = ""
            for g in self.groups:
                if len(g) > 1:
                    for e in g[:-1]:
                        str += "%s," % e
                    str += "%s" % g[-1]
                else:
                    str += "%s" % g[0]
                str += "\n"

            return str
        else:
            return ""


class MyApp(wx.App):
    def OnInit(self):
        self.frame = ChooseGroupsFrame(None, title="Main Frame")
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True


if __name__ == "__main__":
    items = ["Foo", "Bar", "Baz", "Zif", "Zaf", "Zof"]

    app = MyApp(redirect=False)
    app.MainLoop()
