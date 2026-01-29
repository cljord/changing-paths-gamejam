# 1. Setup

import pygame
import moderngl
import numpy as np
                                                                                                      
WIDTH, HEIGHT = 800, 600
pygame.init()
pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
ctx = moderngl.create_context()                                                                      
                                                                                                      
#2. Shaders                                                                                            
                                                                                                      
VERT = """                                                                                            
#version 330                                                                                          
in vec2 in_pos;                                                                                      
in vec2 in_uv;                                                                                        
out vec2 v_uv;                                                                                        
                                                                                                      
uniform vec2 u_pos;                                                                                  
uniform vec2 u_size;                                                                                  
uniform vec2 u_res;                                                                                  
                                                                                                      
void main() {                                                                                        
    vec2 pixel = in_pos * u_size + u_pos;                                                            
    vec2 clip = (pixel / u_res) * 2.0 - 1.0;                                                          
    clip.y *= -1.0;                                                                                  
    gl_Position = vec4(clip, 0.0, 1.0);                                                              
    v_uv = in_uv;                                                                                    
}                                                                                                    
"""                                                                                                  
                                                                                                      
FRAG = """                                                                                            
#version 330                                                                                          
in vec2 v_uv;                                                                                        
out vec4 f_color;                                                                                    
                                                                                                      
uniform sampler2D u_tex;                                                                              
uniform vec3 u_color;                                                                                
uniform float u_use_tex;                                                                              
                                                                                                      
void main() {                                                                                        
    if (u_use_tex > 0.5) {                                                                            
        f_color = texture(u_tex, v_uv);                                                              
    } else {                                                                                          
        f_color = vec4(u_color, 1.0);                                                                
    }                                                                                                
}                                                                                                    
"""                                                                                                  
                                                                                                      
#3. Quad + Program                                                                                    
                                                                                                      
prog = ctx.program(vertex_shader=VERT, fragment_shader=FRAG)                                          
                                                                                                      
quad = np.array([                                                                                    
    -0.5, -0.5,  0.0, 0.0,                                                                            
      0.5, -0.5,  1.0, 0.0,                                                                            
      0.5,  0.5,  1.0, 1.0,                                                                            
    -0.5, -0.5,  0.0, 0.0,                                                                            
      0.5,  0.5,  1.0, 1.0,                                                                            
    -0.5,  0.5,  0.0, 1.0,                                                                            
], dtype='f4')                                                                                        
                                                                                                      
vbo = ctx.buffer(quad)                                                                                
vao = ctx.vertex_array(prog, [(vbo, '2f 2f', 'in_pos', 'in_uv')])                                    
                                                                                                      
# 4. Load Texture                                                                                      
                                                                                                      
def load_texture(path):                                                                              
    surf = pygame.image.load(path).convert_alpha()                                                    
    surf = pygame.transform.flip(surf, False, True)                                                  
    data = pygame.image.tostring(surf, 'RGBA', True)                                                  
    tex = ctx.texture(surf.get_size(), 4, data)                                                      
    tex.filter = (moderngl.NEAREST, moderngl.NEAREST)                                                
    return tex                                                                                        
                                                                                                      
#5. Draw Functions                                                                                    
                                                                                                      
def draw_rect(x, y, w, h, color):                                                                    
    prog['u_pos'].value = (x, y)                                                                      
    prog['u_size'].value = (w, h)                                                                    
    prog['u_res'].value = (WIDTH, HEIGHT)                                                            
    prog['u_color'].value = color                                                                    
    prog['u_use_tex'].value = 0.0                                                                    
    vao.render()                                                                                      
                                                                                                      
def draw_sprite(tex, x, y, w, h):                                                                    
    prog['u_pos'].value = (x, y)                                                                      
    prog['u_size'].value = (w, h)                                                                    
    prog['u_res'].value = (WIDTH, HEIGHT)                                                            
    prog['u_use_tex'].value = 1.0                                                                    
    tex.use(0)                                                                                        
    prog['u_tex'].value = 0                                                                          
    vao.render()                                                                                      
                                                                                                      
#6. Game Loop                                                                                          
                                                                                                      
clock = pygame.time.Clock()                                                                          
running = True                                                                                        
                                                                                                      
x, y = 100, 100

while running:                                                                                        
    dt = clock.tick(60) / 1000.0                                                                      
                                                                                                      
    for event in pygame.event.get():                                                                  
        if event.type == pygame.QUIT:                                                                
            running = False                                                                          

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                y += 10
            if event.key == pygame.K_UP:
                y -= 10
            if event.key == pygame.K_LEFT:
                x -= 10
            if event.key == pygame.K_RIGHT:
                x += 10
                                                                                                      
    # Update game objects here                                                                        
                                                                                                      
    ctx.clear(0.1, 0.1, 0.1)                                                                          
                                                                                                      
    # Draw calls here                                                                                
    draw_rect(x, y, 50, 50, (1.0, 1.0, 1.0))                                                      
                                                                                                      
    pygame.display.flip()                                                                            
                                                                                                      
pygame.quit()      
