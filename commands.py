import sublime
import sublime_plugin

MAX_HIST_SIZE = 5000


class RegionsManager(object):
  def __init__(self):
    self.regions = {}

  def add(self, view, region, contents):
    view_id = view.id()
    regions = self.regions
    contents = [ s for s in contents ]

    if view_id not in regions:
      regions[view_id] = {}

    # print( 'Adding region', contents )
    regions[view_id][region] = contents

  def get(self, view, region):
    view_id = view.id()
    regions = self.regions

    if view_id in regions:
      if region in regions[view_id]:
        # print( 'Getting region', regions[view_id][region] )
        return regions[view_id][region]

    return []

  def erase(self, view, region):
    view_id = view.id()
    regions = self.regions

    if view_id in regions:
      if region in regions:
        # print( 'Deleting region', regions[view_id][region] )
        del regions[view_id][region]

all_regions = RegionsManager()


class History():
  def __init__(self):
    self.index = 0
    self.start = 0
    self.max = 0

  def remove_oldest(self):
    self.start = self.start + 1
    return (self.start - 1)

  def increment(self):
    self.max += 1
    self.index = self.max

  def size(self):
    return self.max - self.start


class Collection():
  def __init__(self):
    self.list = {}
    self.index = 0

  def get(self, view):
    id = view.id()
    if id not in self.list:
      self.list[id] = History()

    return self.list[id]

collection = Collection()


class GotoLastEditEnhanced(sublime_plugin.TextCommand):
  def run(self, edit, backward = False):
    view = self.view
    history = collection.get(view)
    history_range = reversed(range(history.start, history.index + 1))

    if backward:
      history_range = range(history.index, history.max + 1)

    is_lasted = True
    for index in history_range:
      regions = all_regions.get( view, 'goto_last_edit_%s' % index )

      if self.is_regions_equal(regions, view.sel()):
       continue

      is_lasted = False
      if len(regions) > 0:
        sublime.status_message("")
        view.sel().clear()
        view.sel().add_all(regions)
        view.show(regions[0])

        history.index = index
        break
      else:
        sublime.status_message('Already at the ' + ( 'oldest' if backward else 'newest' ) + ' position.')

    if is_lasted:
      sublime.status_message('Already at the ' + ( 'newest' if backward else 'oldest' ) + ' position.')

  def is_regions_equal(self, regions_1, regions_2):
    if len(regions_1) != len(regions_2):
      return False

    for index, region_1 in enumerate(regions_1):
      region_2 = regions_2[index]

      if region_2.a != region_1.a or region_2.b != region_1.b:
        return False

    return True


class Listener(sublime_plugin.EventListener):
  def on_modified(self, view):
    history = collection.get(view)

    if history.size() >= MAX_HIST_SIZE:
      oldest = history.remove_oldest()
      all_regions.erase( view, 'goto_last_edit_%s' % oldest )

    history.increment()
    all_regions.add( view, 'goto_last_edit_%s' % history.index, view.sel() )
