#
# (c) Copyright 2015 Hewlett Packard Enterprise Development Company LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#


class Layer(object):
    def __init__(self, box, dst_x, dst_y):
        self._box = box
        self._dst_x = dst_x
        self._dst_y = dst_y

    def __getitem__(self, y):
        return self._box[y]

    @property
    def box(self):
        return self._box

    @property
    def dst_y(self):
        return self._dst_y

    @property
    def dst_x(self):
        return self._dst_x


class Box(object):
    def __init__(self, w, h):
        self._box = []
        self._title = None
        self._width = w
        self._height = h

        self._layers = []

        for y in range(h):
            self._box.append([])
            for x in range(w):
                self._box[y].append(' ')

        self._draw_outline()

    def __getitem__(self, y):
        return self._box[y]

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def set_title(self, title):
        try:
            if len(title) > self._width:
                max_width = self._width - 4  # borders and spaces
                title = title[0:max_width]

            self._title = title

            x = 2
            while x < len(self._title) + 2:
                self._box[0][x] = self._title[x - 2]
                x += 1
        except:
            pass

    def add_string_absolute(self, text, x, y):
        try:
            if (len(text) + x) > self._width:
                max_width = self._width - 4  # borders and spaces
                text = text[0:max_width]

            src_x = 0
            while src_x < len(text):
                self._box[y][x + src_x] = text[src_x]
                src_x += 1
        except:
            pass

    def add_string_centered(self, text, y, forced_width=None):
        center = (self._width / 2)

        if forced_width:
            x = center - (forced_width / 2) - 1
        else:
            x = center - (len(text) / 2) - 1

        self.add_string_absolute(text, x, y)

    def get_centered_pos(self, text, y, forced_width=None):
        center = (self._width / 2)

        if forced_width:
            x = center - (forced_width / 2) - 1
        else:
            x = center - (len(text) / 2) - 1

        return x, y

    def add_layer(self, box, dst_x, dst_y):
        layer = Layer(box, dst_x, dst_y)
        self._layers.append(layer)

    def flatten(self):
        try:
            for l in reversed(self._layers):
                l.box.flatten()

            for l in reversed(self._layers):
                for y in range(l.box.height):
                    for x in range(l.box.width):
                        self._box[l.dst_y + y][l.dst_x + x] = l.box[y][x]
        except:
            pass

    def display(self, fp=None):
        self.flatten()

        for y in range(self._height):
            if fp:
                fp.write('%s\n' % ''.join(self._box[y]))
            else:
                print('%s' % ''.join(self._box[y]))

        if fp:
            fp.write('\n')
        else:
            print('\n')

    def _draw_outline(self):
        try:
            self._box[0][0] = '+'
            self._box[self._height - 1][0] = '+'
            self._box[0][self._width - 1] = '+'
            self._box[self._height - 1][self._width - 1] = '+'

            x = 1
            while x < self._width - 1:
                self._box[0][x] = '-'
                self._box[self._height - 1][x] = '-'
                x += 1

            y = 1
            while y < self._height - 1:
                self._box[y][0] = '|'
                self._box[y][self._width - 1] = '|'
                y += 1
        except:
            pass
