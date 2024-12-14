import pygame
import random
import math
from queue import PriorityQueue, Queue

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 30, 30
CELL_SIZE = WIDTH // COLS

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Pygame Setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pathfinding Visualization")
clock = pygame.time.Clock()

# Node States
START, END, WALL, PATH, PROCESSING = 1, 2, 3, 4, 5

class Node:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.state = 0  # 0: empty, 1: start, 2: end, 3: wall, 4: path, 5: processing
        self.distance = float("inf")
        self.heuristic = 0
        self.prev = None

    def __lt__(self, other):
        return self.distance < other.distance  # Compare based on distance

    def draw(self):
        color = self.get_color()
        pygame.draw.rect(screen, color, (self.col * CELL_SIZE, self.row * CELL_SIZE, CELL_SIZE - 1, CELL_SIZE - 1))

    def get_color(self):
        if self.state == START:
            return GREEN
        elif self.state == END:
            return RED
        elif self.state == WALL:
            return BLACK
        elif self.state == PATH:
            return YELLOW
        elif self.state == PROCESSING:
            return GRAY
        return WHITE

    def reset(self):
        self.state = 0  # Reset to empty
        self.prev = None
        self.distance = float("inf")
        self.heuristic = 0

class Grid:
    def __init__(self):
        self.grid = [[Node(row, col) for col in range(COLS)] for row in range(ROWS)]
        self.start = None
        self.end = None

    def draw(self):
        for row in self.grid:
            for node in row:
                node.draw()
        for x in range(0, WIDTH, CELL_SIZE):
            pygame.draw.line(screen, GRAY, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, CELL_SIZE):
            pygame.draw.line(screen, GRAY, (0, y), (WIDTH, y))

    def get_neighbors(self, node):
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
        for dr, dc in directions:
            r, c = node.row + dr, node.col + dc
            if 0 <= r < ROWS and 0 <= c < COLS and self.grid[r][c].state != WALL:
                neighbors.append(self.grid[r][c])
        return neighbors

    def reset(self):
        for row in self.grid:
            for node in row:
                node.reset()  # Reset each node
        self.start = None
        self.end = None

class PathfindingVisualizer:
    def __init__(self):
        self.grid = Grid()
        self.info_panel = InfoPanel(screen, WIDTH, HEIGHT)
        self.running = True
        self.visited_count = 0
        self.path_length = 0
        self.show_ui = True  # Flag to control UI visibility

    def run(self):
        while self.running:
            self.handle_events()
            self.update_display()

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click()
            elif event.type == pygame.KEYDOWN:
                self.handle_key_press(event)

    def handle_mouse_click(self):
        x, y = pygame.mouse.get_pos()
        col, row = x // CELL_SIZE, y // CELL_SIZE
        node = self.grid.grid[row][col]

        if node.state == 0:  # Only place if the node is empty
            if not self.grid.start:  # Place start if not already placed
                node.state = START
                self.grid.start = node
            elif not self.grid.end:  # Place end if not already placed
                node.state = END
                self.grid.end = node
            else:  # If both are placed, place walls
                node.state = WALL

    def handle_key_press(self, event):
        if event.key == pygame.K_d and self.grid.start and self.grid.end:
            self.run_algorithm(self.dijkstra)
        elif event.key == pygame.K_a and self.grid.start and self.grid.end:
            self.run_algorithm(self.a_star)
        elif event.key == pygame.K_b and self.grid.start and self.grid.end:
            self.run_algorithm(self.bfs)
        elif event.key == pygame.K_f and self.grid.start and self.grid.end:
            self.run_algorithm(self.dfs)
        elif event.key == pygame.K_c:
            self.grid.reset()  # Clear the grid without resetting start and end
        elif event.key == pygame.K_r:  # Reset build
            self.grid.reset()  # Reset all nodes and clear everything

    def run_algorithm(self, algorithm):
        self.show_ui = False  # Hide UI during algorithm execution
        self.visited_count = algorithm()
        self.show_ui = True  # Show UI again after execution
        self.show_popup(f"Visited Nodes: {self.visited_count}\nPath Length: {self.path_length}")

    def show_popup(self, message):
        font = pygame.font.SysFont("Arial", 30)
        text_surface = font.render(message, True, BLACK)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        
        # Create a semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill((255, 255, 255, 180))  # White with some transparency
        screen.blit(overlay, (0, 0))
        
        # Draw the text
        screen.blit(text_surface, text_rect)
        pygame.display.update()

        # Wait for a key press to close the popup
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                if event.type == pygame.KEYDOWN:
                    waiting = False

    def update_display(self):
        screen.fill(WHITE)
        self.grid.draw()  # Draw the grid first
        self.info_panel.draw(self.visited_count, self.path_length)  # Draw the info panel
        pygame.display.update()

    def dijkstra(self):
        open_set = PriorityQueue()
        self.grid.start.distance = 0
        open_set.put(self.grid.start)
        visited_count = 0

        while not open_set.empty():
            current = open_set.get()

            if current == self.grid.end:
                self.path_length = self.reconstruct_path(current)
                return visited_count

            current.state = PROCESSING
            visited_count += 1
            self.grid.draw()
            pygame.display.update()
            clock.tick(60)

            for neighbor in self.grid.get_neighbors(current):
                temp_distance = current.distance + 1
                if temp_distance < neighbor.distance:
                    neighbor.distance = temp_distance
                    neighbor.prev = current
                    open_set.put(neighbor)

        return 0  # Return 0 if no path found

    def a_star(self):
        open_set = PriorityQueue()
        self.grid.start.distance = 0
        open_set.put(self.grid.start)
        visited_count = 0

        while not open_set.empty():
            current = open_set.get()

            if current == self.grid.end:
                self.path_length = self.reconstruct_path(current)
                return visited_count

            current.state = PROCESSING
            visited_count += 1
            self.grid.draw()
            pygame.display.update()
            clock.tick(60)

            for neighbor in self.grid.get_neighbors(current):
                temp_distance = current.distance + 1
                if temp_distance < neighbor.distance:
                    neighbor.distance = temp_distance
                    neighbor.prev = current
                    neighbor.heuristic = self.heuristic(neighbor, self.grid.end)
                    open_set.put(neighbor)

        return 0  # Return 0 if no path found

    def heuristic(self, node_a, node_b):
        # Using Manhattan distance as heuristic
        return abs(node_a.row - node_b.row) + abs(node_a.col - node_b.col)

    def bfs(self):
        queue = Queue()
        queue.put(self.grid.start)
        visited_count = 0
        visited = set()
        visited.add(self.grid.start)

        while not queue.empty():
            current = queue.get()

            if current == self.grid.end:
                self.path_length = self.reconstruct_path(current)
                return visited_count

            current.state = PROCESSING
            visited_count += 1
            self.grid.draw()
            pygame.display.update()
            clock.tick(60)

            for neighbor in self.grid.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    neighbor.prev = current
                    queue.put(neighbor)

        return 0  # Return 0 if no path found

    def dfs(self):
        stack = [self.grid.start]
        visited_count = 0
        visited = set()

        while stack:
            current = stack.pop()

            if current == self.grid.end:
                self.path_length = self.reconstruct_path(current)
                return visited_count

            if current not in visited:
                visited.add(current)
                current.state = PROCESSING
                visited_count += 1
                self.grid.draw()
                pygame.display.update()
                clock.tick(60)

                for neighbor in self.grid.get_neighbors(current):
                    if neighbor not in visited:
                        neighbor.prev = current
                        stack.append(neighbor)

        return 0  # Return 0 if no path found

    def reconstruct_path(self, node):
        path_length = 0
        while node:
            if node.state not in (START, END):
                node.state = PATH
                path_length += 1
            node = node.prev
            self.grid.draw()
            pygame.display.update()
            clock.tick(20)
        return path_length

class InfoPanel:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont("Arial", 20)

    def draw(self, visited_count, path_length):
        pygame.draw.rect(self.screen, GRAY, (self.width - 200, 0, 200, self.height))
        controls_text = [
            "Controls:",
            "Left Click: Place Start/End/Walls",
            "D: Run Dijkstra's Algorithm",
            "A: Run A* Algorithm",
            "B: Run BFS",
            "F: Run DFS",
            "C: Clear Grid",
            "R: Reset Build"
        ]

        for i, line in enumerate(controls_text):
            text_surface = self.font.render(line, True, BLACK)
            self.screen.blit(text_surface, (self.width - 190, 20 + i * 30))

        result_text = f"Visited: {visited_count}, Path Length: {path_length}"
        result_surface = self.font.render(result_text, True, BLACK)
        self.screen.blit(result_surface, (self.width - 190, 20 + len(controls_text) * 30))

if __name__ == "__main__":
    visualizer = PathfindingVisualizer()
    visualizer.run()