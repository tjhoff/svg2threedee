import stl
import xml.etree.cElementTree
import logging
import math

import triangulate

class Path:
    def __init__(self, sections = None):
        if sections is None:
            self.sections = []
        else:
            self.sections = sections

    def __repr__(self):
        return "Path with {} sections: {}".format(len(self.sections), self.sections)

    def size(self):
        max_x = 0
        min_x = None
        max_y = 0
        min_y = None
        for section in self.sections:
            for coordinate in section:
                if min_x is None or min_y is None:
                    min_x = coordinate.x
                    min_y = coordinate.y
                max_x = max(coordinate.x, max_x)
                min_x = min(coordinate.x, min_x)
                max_y = max(coordinate.y, max_y)
                min_y = min(coordinate.y, min_y)
        print(max_x, min_x, max_y, min_y)
        return max_x - min_x, max_y - min_y

    def translate_all(self, tx):
        for section in self.sections:
            for coordinate in section:
                coordinate.translate(tx)

class Vector2D:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    @staticmethod
    def from_vector(v):
        return Vector2D(v.x, x.y)

    def translate(self, coordinate):
        self.x += coordinate.x
        self.y += coordinate.y

    def copy(self):
        return Vector2D.from_vector(self)

    def __repr__(self):
        if self.x is None or self.y is None:
            return "(invalid)"
        return "({:3.2f}, {:3.2f})".format(self.x, self.y)

    def __getitem__(self, key):
        return [self.x, self.y][key]

class Vector3D:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def from_2d_with_z(v, z):
        return Vector3D(v.x, v.y, z)

    def sub(self, v):
        return Vector3D(self.x-v.x, self.y-v.y, self.z-v.z)

    def cross(self, v):
        return self.x*v.x + self.y*v.y + self.z*v.z

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalize(self):
        length = self.length()
        if length == 0:
            return Vector3D(0,0,0)
        return Vector3D(self.x/length, self.y/length, self.z/length)

    def __repr__(self):
        if self.x is None or self.y is None or self.z is None:
            return "(invalid)"
        return "({:3.2f}, {:3.2f}, {:3.2f})".format(self.x, self.y, self.z)

    def as_list(self):
        return [self.x, self.y, self.z]

    def copy(self):
        return Vector3D(self.x, self.y, self.z)

def get_paths(file):
    print("Loading {0}".format(file))
    tree = xml.etree.cElementTree.parse(file)
    root = tree.getroot()
    width_mm = float(root.get("width").strip("mm"))
    height_mm = float(root.get("height").strip("mm"))
    viewbox = root.get("viewBox").split(" ")
    viewbox = list(map(lambda x: float(x), viewbox))
    logging.debug("{} by {} with viewbox of {}".format(width_mm, height_mm, viewbox))
    x_scale = (viewbox[2]-viewbox[0]) / width_mm
    y_scale = (viewbox[3]-viewbox[1]) / height_mm
    logging.debug("{}x{}y".format(x_scale, y_scale))

    g = root.find('{http://www.w3.org/2000/svg}g')
    print(g)
    for child in g:
        print(child)
    paths = g.findall('{http://www.w3.org/2000/svg}path')
    paths = g.findall('.//{http://www.w3.org/2000/svg}path')
    print(paths)
    svg_paths = []
    for path in paths:
        print("Getting path")
        svg_paths.append(parse_path(path.get("d"), x_scale, y_scale))

    return svg_paths

def parse_path(path_str, x_scale = 1, y_scale = 1):
    # "M" or "m" means start of path
    # "z" means end of path
    # "L" means line segment
    # TODO- deal with more advanced elements later

    parts = path_str.split(" ")
    sections = []
    current_section = []
    current_coordinate = Vector2D(None, None)
    x_pos = 0
    y_pos = 0
    lineto_relative = True
    for part in parts:
        if not part:
            continue
        if part == "m":
            print("relative moveto")
            # finish the current section
            if current_section:
                sections.append(current_section)
            current_section = []
            current_coordinate = Vector2D(None, None)
            lineto_relative = True
        elif part == "M":
            print("Absolute moveto")
            # finish the current section
            if current_section:
                sections.append(current_section)
            current_section = []
            current_coordinate = Vector2D(None, None)
            lineto_relative = False
        elif part.lower() == "z":
            # finish the current section
            if current_section:
                sections.append(current_section)
            current_section = []
            current_coordinate = Vector2D(None, None)
        elif part == "l":
            print("\trelative lineto")
            # relative coordinates from here on
            if current_coordinate.x is not None and current_coordinate.y is not None:
                current_section.append(current_coordinate)
            current_coordinate = Vector2D(None, None)
            lineto_relative = True
        elif part == "L":
            print("\tabsolute lineto")
            # absolute coordinates from here on
            if current_coordinate.x is not None and current_coordinate.y is not None:
                current_section.append(current_coordinate)
            current_coordinate = Vector2D(None, None)
            lineto_relative = False
        elif "," in part:
            # add an x/y coordinate with the current offset
            x, y = part.split(",")

            if lineto_relative and current_section:
                # we're past the first element in a relative moveto section and part of a relative lineto section
                x = x_pos = x_pos + float(x)/x_scale
                y = y_pos = y_pos + float(y)/y_scale
            else:
                # we're either the first element in a moveto section, or part of an absolute lineto section
                x_pos = x = float(x)/x_scale
                y_pos = y = float(y)/y_scale
            current_coordinate = Vector2D(x,y)
            current_section.append(current_coordinate)
            current_coordinate = Vector2D(None, None)
        else:
            # complete the current coordinate
            assert(current_coordinate.y is None)
            if current_coordinate.x is not None:
                current_coordinate.y = float(part) / y_scale
            else:
                current_coordinate.x = float(part) / x_scale

    if current_coordinate.x is not None and current_coordinate.y is not None:
        current_section.append(current_coordinate)
    if current_section:
        sections.append(current_section)

    # Set the first coordinate to 0,0
    path = Path(sections)
    first_coord = path.sections[0][0]
    tx = Vector2D(-first_coord.x, -first_coord.y)
    path.translate_all(tx)
    return path

def triangleize(path, height):
    # TODO
    # first - determine nesting and if any paths intersect other paths (this will be an error case)
    # second - triangleize the strips of sections according to their nesting order and the model height
    # p2--p4
    # |  / |
    # | /  |
    # p1--p3
    triangles = []
    for section in path.sections:

        for i in range(len(section)):
            i1 = i
            if i >= len(section) - 1:
                i2 = 0
            else:
                i2 = i + 1

            p1 = Vector3D.from_2d_with_z(section[i1], 0)
            p2 = Vector3D.from_2d_with_z(section[i1], height)
            p3 = Vector3D.from_2d_with_z(section[i2], 0)
            p4 = Vector3D.from_2d_with_z(section[i2], height)

            t1 = [p1.copy(), p4.copy(), p2.copy()]
            t2 = [p1.copy(), p3.copy(), p4.copy()]
            triangles.append(t1)
            triangles.append(t2)

        face = []
        while section:
            ear = triangulate.GetEar(section)
            if not ear:
                break
            face.append(ear)
        # create top face
        for ear in face:
            triangle = [Vector3D.from_2d_with_z(ear[0], height),
                        Vector3D.from_2d_with_z(ear[1], height),
                         Vector3D.from_2d_with_z(ear[2], height)]
            triangles.append(triangle)
        # create bottom face
        for ear in face:
            triangle = [Vector3D.from_2d_with_z(ear[0], 0),
                        Vector3D.from_2d_with_z(ear[2], 0),
                         Vector3D.from_2d_with_z(ear[1], 0)]
            triangles.append(triangle)

    # third - create top and bottom faces

    return triangles

def normal_from_triangle(triangle):
    p1,p2,p3 = triangle
    v = p2.sub(p1)
    w = p3.sub(p3)
    nx = (v.y * w.z) - (v.z * w.y)
    ny = (v.z * w.x) - (v.x * w.z)
    nz = (v.x * w.y) - (v.y * w.x)
    n = Vector3D(nx, ny, nz).normalize()
    return n

def stl_from_triangles(triangles):
    facets = []
    for triangle in triangles:
        normal = normal_from_triangle(triangle)
        facet = stl.types.Facet(normal.as_list(), [triangle[0].as_list(), triangle[1].as_list(), triangle[2].as_list()])
        facets.append(facet)
    print("{} facets".format(len(facets)))
    return stl.Solid("thing", facets)

def visualize_path(path, name):
    from PIL import Image, ImageDraw
    im_size = path.size()
    offset_x = 100 + im_size[0] * .5
    offset_y = 100 + im_size[1] * .5
    im = Image.new("RGB", (int(offset_x + im_size[0] * 2), int(offset_y + im_size[1] * 2)))
    draw = ImageDraw.Draw(im)
    for section in path.sections:
        for coord_idx in range(len(section)):
            if coord_idx == len(section)-1:
                c1 = section[coord_idx]
                c2 = section[0]
            else:
                c1 = section[coord_idx]
                c2 = section[coord_idx+1]
            draw.line([(c1.x + offset_x/2,c1.y + offset_y/2),(c2.x + offset_x/2,c2.y + offset_y/2)])
    fname = "{}.png".format(name)

    im.save(fname)
    print("Saved a visualization to {}".format(fname))

if __name__ == "__main__":
    import sys
    height = 0
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    if len(sys.argv) > 2:
        height = float(sys.argv[2])
    else:
        print("No correct file path provided - try python {} {} as an example".format(sys.argv[0], "test_svg/gear.svg"))
    paths = get_paths(file_path)

    i = 0
    for path in paths:
        solid = stl_from_triangles(triangleize(path, height))
        with open("path_{}.stl".format(i), "w") as f:
            solid.write_ascii(f)
        i+=1
