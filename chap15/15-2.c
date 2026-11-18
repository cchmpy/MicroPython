#include "py/runtime.h"
#include "py/binary.h"
#include "py/objlist.h"
#include "py/objtuple.h"
#include "py/gc.h"
#include <string.h>   // memset
#include <stdint.h>   // uint8_t
#include <stdbool.h>  // bool
/*
*  模块名称：track
*  类 名 称：TrackImage、Blob
*/

// ================================ 第1部分：宏定义 ================================
#define REGION_COUNT    6       // 水平区域数量(0~5),图像最下面为区域0
#define MAX_WIDTH       160     // 最大图像宽度
#define MAX_HEIGHT      120     // 最大图像高度
#define MAX_BLOBS       16      // 最大色块数量

// ================================ 第2部分：寻找色块核心算法 =======================
// 栈结构体:用于扫描线填充,存储待处理行号(y坐标)和种子点
typedef struct {
    int y[MAX_HEIGHT];          // 存储行号
    int x[MAX_HEIGHT];          // (x,y)是该行对应种子点
    int top;                    // 上述数组的索引值(表示栈顶)
} Stack;

// 色块信息结构体(存储最终结果) 
typedef struct {
    int region_id;              // 所属区域ID(0~5)
    int x,y,w,h;                // 色块矩形信息
    int cx, cy;                 // 中心坐标
    int pixels;                 // 符合颜色要求的有效像素数量
    int area;                   // 色块面积w*h
    int _top_left,_top_right;   // 色块顶部有效像素的左右x坐标，用于寻找下个区域色块（线路是连续的）
} ColorBlock;

// 寻找色块的核心函数：find_blobs_core()，C代码内部函数，MicroPython无法直接调用
static int find_blobs_core(uint8_t *image, int w, int h,
                int threshold, int x_stride, int y_stride,
                int area_thr, int pixels_thr, bool invert,
                Stack *stack, ColorBlock *blocks, bool *visited){
    // 初始化全局变量、定义局部变量
    memset(visited, 0, w*h*sizeof(bool));      // 重置访问标记数组        
    int region_h = h/REGION_COUNT;             // 每个区域的高度
    int blk_cnt = 0;                           // 当前图像包含色块的数量
    int search_x_start = 0;                    // 搜索当前区域的起始x
    int search_x_end = w - 1;                  // 搜索当前区域的结束x    
    int c = invert ? -1 : 1;                   // 预先计算符号,用于阈值判断
        
    for(int id=0; id<REGION_COUNT; id++){      // 循环查找6个区域
        int y_bottom=h-1-id*region_h;          // 当前区域底部y坐标
        int y_top = y_bottom+1-region_h;       // 当前区域顶部y坐标        
        
        if(blk_cnt>0){                         // 底部区域已经发现色块
            if(blocks[blk_cnt-1].region_id != id-1) break; // 若上一个区域没有发现色块，退出（前方没有路，弯道）
            search_x_start = MAX(blocks[blk_cnt-1]._top_left-10,0);  // 左侧坐标增加冗余量10
            search_x_end = MIN(blocks[blk_cnt-1]._top_right+10,w-1); // 右侧坐标增加冗余量10
        }
               
        for(int y=y_bottom; y>=y_top; y-=y_stride){                   // 遍历区域内的所有行
            // 如果上个区域和本区域都有色块，则不用继续查找，直接退出（当前区域只需找到1个色块）
            if(blk_cnt>1 && blocks[blk_cnt-2].region_id == id-1 && blocks[blk_cnt-1].region_id == id) break;
            
            for(int x=search_x_start; x<=search_x_end; x+=x_stride){  // 遍历指定范围内的列
                                 
                // 找到没有访问过的目标像素(种子点)，用于扫描线填充
                int idx = y*w+x;                     // 当前像素点
                if(c*(image[idx]-threshold)<0 && !visited[idx] ) {
                    stack->top = -1;                 // 初始化栈(行号) 
                    stack->y[++stack->top] = y;      // 把当前行压栈（压栈）
                    stack->x[stack->top] = x;        // 当前行的种子点
                          
                    visited[idx] = true;             // 标记该像素已被访问
                    int pixels = 0;                  // 当前色块包含有效像素数                    
                    int min_x = x, max_x = x, min_y = y, max_y = y; // 初始化色块包围矩形
                    int left=x, right=x;                 // 当前行中，目标颜色线段左右两端的x坐标          

                    // 扫描线填充的核心逻辑，从种子点开始查找一个色块
                    while (stack->top > -1) {                   // 栈不为空
                        int seed_y = stack->y[stack->top];       // 当前要处理的行(种子行) 
                        int seed_x = stack->x[stack->top--];     // 当前行种子点、出栈 
                        left=seed_x; right = seed_x;             // 初始化种子点左右两侧的x坐标

                        // 1. 向左扩展
                        while (left>= 0 && c*(image[seed_y*w+left-1]-threshold)<0 && !visited[seed_y*w+left-1]) {
                            left--;  pixels++;                            
                            visited[seed_y*w+left] = true;                            
                        }
                        // 2. 向右扩展
                        while (right + 1 < w && c*(image[seed_y*w+right+1]-threshold)<0 && !visited[seed_y*w+right+1]) {
                            right++; pixels++;                            
                            visited[seed_y*w+right] = true;
                        }                        
                        // 4. 用当前线更新包围矩形                        
                        if (left < min_x) min_x = left;
                        if (right > max_x) max_x = right;
                        if (seed_y < min_y) min_y = seed_y;
                        if (seed_y > max_y) max_y = seed_y;

                        // 5. 检查上下行，寻找新种子点
                        for (int dy = -1; dy <= 1; dy += 2) {
                            int ny = seed_y + dy;
                            if (ny < y_top || ny > y_bottom) continue; // 仅处理当前区域
                            for (int nx = left; nx <= right; nx++) {
                                int i = ny*w+nx;                                
                                if (c*(image[i]-threshold)<0 && !visited[i]) {
                                    visited[i] = true;                                    
                                    stack->y[++stack->top] = ny;      // 把当前行压栈（压栈）
                                    stack->x[stack->top] = nx;        // 当前行的种子点                                                                       
                                    break;                            // 仅压栈1个种子点
                                }
                            }
                        }
                    }
                    // 计算色块参数                    
                    ColorBlock b;
                    b.region_id = id;
                    b.x = min_x;
                    b.y = min_y;
                    b.w = max_x - min_x + 1;
                    b.h = max_y - min_y + 1;
                    b.cx = min_x + b.w / 2;    // 中心x坐标
                    b.cy = min_y + b.h / 2;
                    b.pixels = pixels;         // 符合颜色要求的有效像素数量
                    b.area = b.w * b.h;       // 色块面积w*h  
                    b._top_left = left;        
                    b._top_right = right;             
                    
                    // 检查色块是否合规, 每个区域只保留1个色块（首个区域保留最大的，后续区域查到1个色块就退出）
                    if (b.pixels>pixels_thr && b.area>area_thr) {                        
                        if(blk_cnt==0) {                            
                            memcpy(&blocks[blk_cnt++], &b, sizeof(ColorBlock));  // 第一个色块
                        }    
                        else{
                            if(blocks[blk_cnt-1].region_id == id){    // 同区域色块（只保留一个色块，blk_cnt不增加）
                                if(b.area > blocks[blk_cnt-1].area){                                    
                                    memcpy(&blocks[blk_cnt-1], &b, sizeof(ColorBlock)); }
                            }else {                                    // 不同区域色块
                                memcpy(&blocks[blk_cnt++], &b, sizeof(ColorBlock)); } 
                        }
                        // 如果上个区域有色块，则退出(本区域已经添加了色块)
                        if(blk_cnt>1 && blocks[blk_cnt-2].region_id == id-1) {
                            break; }
                    }                    
                    x = max_x;      // 在当前行内，直接跳转到当前色块右侧，继续遍历
                }
            }
        }
    }      
    return blk_cnt;
}


// ================================ 第3部分：定义Blob类 ============================
// Blob类的结构体
typedef struct _track_Blob_obj_t {
    mp_obj_base_t base;          // 所有MicroPython对象的标准对象头，必须放在结构体的首位
    // 以下字段都是对象的属性，但MicroPython代码无法直接访问（需借助属性或方法）       
    ColorBlock data;
} track_Blob_obj_t;              // c内部类名（结构体名）

// 属性访问控制函数attr：track_Blob_attribute()，实现只读、白名单、隐藏内部字段
static void track_Blob_attribute(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {
    track_Blob_obj_t *self = MP_OBJ_TO_PTR(self_in);    
    if (dest[0] != MP_OBJ_NULL) return;      // 直接忽略写入或删除属性的操作
    
    switch (attr) {                          // 处理属性读取操作 (白名单,仅暴露以下公开属性)
        case MP_QSTR_region_id:
            dest[0] = mp_obj_new_int(self->data.region_id); break;
        case MP_QSTR_x:
            dest[0] = mp_obj_new_int(self->data.x); break;
        case MP_QSTR_y:
            dest[0] = mp_obj_new_int(self->data.y); break;        
        case MP_QSTR_w:
            dest[0] = mp_obj_new_int(self->data.w); break;
        case MP_QSTR_h:
            dest[0] = mp_obj_new_int(self->data.h); break;
        case MP_QSTR_cx:
            dest[0] = mp_obj_new_int(self->data.cx); break;
        case MP_QSTR_cy:
            dest[0] = mp_obj_new_int(self->data.cy); break;
        case MP_QSTR_pixels:
            dest[0] = mp_obj_new_int(self->data.pixels); break;
        case MP_QSTR_area:
            dest[0] = mp_obj_new_int(self->data.area); break;
        default:
            dest[0] = MP_OBJ_NULL;          // 如果为空，MicroPython自动抛出AttributeError
    }    
}

// Blob类的类型定义
MP_DEFINE_CONST_OBJ_TYPE(        // 定义类的顶级宏，类似Python的class TrackImage
    track_type_Blob,             // 参数1：C语言层面类名（模块名_type_类名）
    MP_QSTR_Blob,                // 参数2：Python层面类名（MP_QSTR_类名）
    MP_TYPE_FLAG_NONE,           // 参数3：类型标志位。为类添加内置特性，如是否可迭代等。
    attr, track_Blob_attribute   // 参数4、5：键值对，定义属性访问    
);

// C内部函数：将C语言的ColorBlock结构体包装成Python对象
static mp_obj_t blob_new_from_c(const ColorBlock *blk) {
    track_Blob_obj_t *self = m_new_obj(track_Blob_obj_t);
    self->base.type = &track_type_Blob;
    self->data = *blk;                     // 注意，*blk，会深拷贝数据
    return MP_OBJ_FROM_PTR(self);
}

// ================================ 第4部分：定义TrackImage类 ======================
// TrackImage类的结构体
typedef struct _track_TrackImage_obj_t {
    mp_obj_base_t base;
    mp_obj_t buf_obj;             // 图像缓冲区
    int width;
    int height;
    bool copy;                    // 是否拷贝源缓冲数据到buf_obj
    // 需要在构造方法中动态分配内存的数据项
    bool *visited;                // 布尔数组，标记已访问像素，长度=width*height
    ColorBlock *blocks;           // 保存所有色块数量，最多32个
    Stack *stack;                 // 栈
    mp_obj_t result_list;         // 预分配保存查找结果的列表
} track_TrackImage_obj_t;         // c内部类名（结构体名）

// 类的构造方法: make_new()
static mp_obj_t track_TrackImage_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    // 1. 定义参数解析表：{参数名, 类型, 标志, 默认值}    
    enum { ARG_width, ARG_height, ARG_buffer, ARG_copy };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_width,  MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },     // 必选位置参数0: width
        { MP_QSTR_height, MP_ARG_REQUIRED | MP_ARG_INT, {.u_int = 0} },     // 必选位置参数1: height
        { MP_QSTR_buffer, MP_ARG_OBJ, {.u_obj = mp_const_none} },           // 可选参数2: buffer (默认None)
        { MP_QSTR_copy,   MP_ARG_KW_ONLY | MP_ARG_BOOL, {.u_bool = true} }, // 可选参数：是否拷贝源数据到buf_obj
    };

    // 2. 解析参数
    mp_arg_val_t vals[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all_kw_array(n_args, n_kw, args, MP_ARRAY_SIZE(allowed_args), allowed_args, vals); // 普通函数使用mp_arg_parse_all解析
    
    // 3. 获取必选参数并做边界检查
    int width = vals[ARG_width].u_int;
    int height = vals[ARG_height].u_int;
    if (width > MAX_WIDTH || height > MAX_HEIGHT || width <= 0 || height <= 0) {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid image size (max 160x120)"));
    }

    // 4. 处理可选缓冲区参数
    mp_obj_t buf_obj = mp_const_none;             // 初始化为 None
    mp_obj_t buffer_arg = vals[ARG_buffer].u_obj;
    bool copy = vals[ARG_copy].u_bool;
    size_t expected_size = (size_t)width * (size_t)height;

    if (buffer_arg != mp_const_none) {
        // 用户提供了缓冲区对象：获取其底层内存并校验（支持 bytes/bytearray/memoryview）
        mp_buffer_info_t src_bufinfo;
        mp_get_buffer_raise(buffer_arg, &src_bufinfo, MP_BUFFER_READ);
        
        if (src_bufinfo.len != expected_size) {
            mp_raise_ValueError(MP_ERROR_TEXT("buffer length does not match width*height"));
        }

        if (copy) {          // 模式1：拷贝（默认）- 创建独立可写 bytearray            
            buf_obj = mp_obj_new_bytearray(src_bufinfo.len, src_bufinfo.buf);
        } else {             // 模式2：零拷贝引用，直接引用任何实现缓冲区协议的对象（bytes/bytearray/memoryview）            
            buf_obj = buffer_arg;
        }
    } else {                 // 用户未提供缓冲对象       
        if (copy) {          // copy=True：创建全零可写 bytearray            
            uint8_t *zero_buf = m_new0(uint8_t, expected_size);
            buf_obj = mp_obj_new_bytearray_by_ref(expected_size, zero_buf);
        } else {             // copy=False：设为 None            
            buf_obj = mp_const_none;
        }
    }
    
    // 5. 创建TrackImage实例及其实例变量
    track_TrackImage_obj_t *self = mp_obj_malloc(track_TrackImage_obj_t, type);
    self->base.type = type;
    self->buf_obj = buf_obj;
    self->width = width;
    self->height = height;
    self->copy = copy;
    
    // 6. 预分配内存
    self->visited = m_new(bool, width * height);
    self->stack = m_new(Stack, 1);
    self->blocks = m_new(ColorBlock, MAX_BLOBS);
    self->result_list = mp_obj_new_list(0, NULL);

    return MP_OBJ_FROM_PTR(self);
}

// 定义类的方法：deinit()，用于释放所有预分配的内存
static mp_obj_t track_TrackImage_deinit(mp_obj_t self_in) {
    track_TrackImage_obj_t *self = MP_OBJ_TO_PTR(self_in);    
    if (self->visited != NULL) {
        m_del(bool, self->visited, self->width*self->height);
        self->visited = NULL;
    }
    if (self->stack != NULL) {
        m_del(Stack, self->stack, 1);
        self->stack= NULL;
    }    
    if (self->blocks != NULL) {
        m_del(ColorBlock, self->blocks, MAX_BLOBS);
        self->blocks = NULL;
    }     
    if (self->copy && self->buf_obj != MP_OBJ_NULL) {        
        mp_buffer_info_t bufinfo;    // 获取bytearray内部的缓冲区指针
        mp_get_buffer_raise(self->buf_obj, &bufinfo, MP_BUFFER_READ);
        m_del(uint8_t, bufinfo.buf, bufinfo.len); // 释放之前分配的内存
        self->buf_obj = MP_OBJ_NULL;
    }   
    // result_list由GC自动回收，无需手动释放    
    return mp_const_none;
}
// 定义该方法的Python引用，宏名称末尾的数字1表示该方法接受1个参数(依此类推)
static MP_DEFINE_CONST_FUN_OBJ_1(track_TrackImage_deinit_obj, track_TrackImage_deinit);

// 定义类的方法：buffer()，获取图像的底层缓冲区对象
static mp_obj_t track_TrackImage_buffer(mp_obj_t self_in) {
    track_TrackImage_obj_t *self = MP_OBJ_TO_PTR(self_in);    
    return self->buf_obj;
}
static MP_DEFINE_CONST_FUN_OBJ_1(track_TrackImage_buffer_obj, track_TrackImage_buffer);

// 定义类的方法：update_image()，更新目标图像，并根据类的布尔属性copy决定是否内存拷贝
static mp_obj_t track_TrackImage_update_image(mp_obj_t self_in, mp_obj_t buf_obj) {
    track_TrackImage_obj_t *self = MP_OBJ_TO_PTR(self_in);
    size_t expected_size = (size_t)self->width * (size_t)self->height;

    // 获取源缓冲区信息（支持 bytes/bytearray/memoryview）
    mp_buffer_info_t src_bufinfo;
    mp_get_buffer_raise(buf_obj, &src_bufinfo, MP_BUFFER_READ);
    
    if (src_bufinfo.len != expected_size) {
        mp_raise_ValueError(MP_ERROR_TEXT("buffer length does not match image size"));
    }

    if (self->copy) {    // 模式1：拷贝数据        
        if (self->buf_obj == mp_const_none) {   // 若当前 buf_obj是None：创建新的 bytearray            
            self->buf_obj = mp_obj_new_bytearray(src_bufinfo.len, src_bufinfo.buf);
        } else {                                // 当前 buf_obj 有效：原地拷贝（避免重新分配内存）
            mp_buffer_info_t dst_bufinfo;
            mp_get_buffer_raise(self->buf_obj, &dst_bufinfo, MP_BUFFER_WRITE);
            memcpy(dst_bufinfo.buf, src_bufinfo.buf, src_bufinfo.len);
        }
    } else {      // 模式2：零拷贝引用 - 直接引用实现缓冲区协议的对象
        self->buf_obj = buf_obj;
    }  
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(track_TrackImage_update_image_obj, track_TrackImage_update_image);

// 定义类的方法：find_blobs()，寻找色块并返回包含Blob对象的列表
static mp_obj_t track_TrackImage_find_blobs(size_t n_args, const mp_obj_t *args, mp_map_t *kw_args) {
    track_TrackImage_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    enum { ARG_threshold, ARG_x_stride, ARG_y_stride, ARG_area_thr, ARG_pixels_thr, ARG_invert }; 
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_threshold, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = 64} },
        { MP_QSTR_x_stride, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = 2} },
        { MP_QSTR_y_stride, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = 2} },
        { MP_QSTR_area_thr, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = 50} },
        { MP_QSTR_pixels_thr, MP_ARG_KW_ONLY | MP_ARG_INT, {.u_int = 20} },
        { MP_QSTR_invert, MP_ARG_KW_ONLY | MP_ARG_BOOL, {.u_bool = false} },
    };
        
    // 解析关键字参数
    mp_arg_val_t args_val[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args - 1, args + 1, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args_val);
    
    int threshold = args_val[ARG_threshold].u_int;
    int x_stride = args_val[ARG_x_stride].u_int;
    int y_stride = args_val[ARG_y_stride].u_int;
    int area_thr = args_val[ARG_area_thr].u_int;
    int pixels_thr = args_val[ARG_pixels_thr].u_int;
    bool invert = args_val[ARG_invert].u_bool;  
    
    int w = self->width;
    int h = self->height;
    
    // 获取图像数据
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(self->buf_obj, &bufinfo, MP_BUFFER_READ);
    uint8_t *image = (uint8_t *)bufinfo.buf;    
      
    // 使用预分配内存调用算法    
    int blk_cnt = find_blobs_core(image, w, h, threshold, x_stride, y_stride, area_thr, pixels_thr, invert,
                                   self->stack, self->blocks, self->visited);
    
    // 填充返回列表
    mp_obj_list_t *list = MP_OBJ_TO_PTR(self->result_list);
    list->len = 0;     // 清空列表    
    for (int i = 0; i < blk_cnt; i++) { 
        mp_obj_list_append(self->result_list, blob_new_from_c(&self->blocks[i]));        
    }   
    
    return self->result_list;
}
// 定义该方法的Python引用，宏名称末尾的KW表示该方法只接受关键字参数
static MP_DEFINE_CONST_FUN_OBJ_KW(track_TrackImage_find_blobs_obj, 1, track_TrackImage_find_blobs);

// 定义类的方法：find_offset()，寻找色块并返回色块数量和权重偏移量(blob_count, dx)
static mp_obj_t track_TrackImage_find_offset(size_t n_args, const mp_obj_t *args, mp_map_t *kw_args) {
    track_TrackImage_obj_t *self = MP_OBJ_TO_PTR(args[0]);

    // 1. 手动从关键字参数中提取 weights，并从参数表中移除它
    mp_obj_t weights_obj = MP_OBJ_NULL;
    if (kw_args != NULL && kw_args->used > 0) {
        // 在关键字参数 map 中查找 weights
        mp_map_elem_t *elem = mp_map_lookup(kw_args, MP_OBJ_NEW_QSTR(MP_QSTR_weights), MP_MAP_LOOKUP);
        if (elem != NULL) {
            weights_obj = elem->value;            
            elem->key = MP_OBJ_NULL; // 【关键】从参数表中移除 weights：将 key 设为 NULL，后续解析会自动忽略
            kw_args->used--;           // 2. 【关键修复】减少 used 计数，让 mp_arg_parse_all 知道少了一个参数
        }
    }

    // 2. 初始化权重
    int weights[REGION_COUNT] = {1, 3, 5, 5, 3, 1}; // 默认权重
    if (weights_obj != MP_OBJ_NULL) {
        size_t len; mp_obj_t *items;
        mp_obj_get_array(weights_obj, &len, &items);
        if (len != REGION_COUNT) {
            mp_raise_ValueError(MP_ERROR_TEXT("weights need 6 nums"));
        }
        for (int i = 0; i < REGION_COUNT; i++) {
            weights[i] = mp_obj_get_int(items[i]);
        }
    }

    // 3. 透传“干净”的参数给 find_blobs（已移除 weights）
    mp_obj_t blobs_list = track_TrackImage_find_blobs(n_args, args, kw_args);
    size_t blob_cnt; mp_obj_t *blob_items;
    mp_obj_get_array(blobs_list, &blob_cnt, &blob_items);

    // 4. 计算权重偏移量
    int img_center_x = self->width / 2;
    int sum_w = 0, sum_wdx = 0; // 防止溢出

    for (size_t i = 0; i < blob_cnt; i++) {
        mp_obj_t blob_obj = blob_items[i];

        // 安全检查：确保是 Blob 类型
        if (!mp_obj_is_type(blob_obj, &track_type_Blob)) {
            continue;
        }

        // 直接通过 C 结构体指针获取数据
        track_Blob_obj_t *blob = MP_OBJ_TO_PTR(blob_obj);
        int rid = blob->data.region_id;
        int cx = blob->data.cx;

        // 区域 ID 合法性校验
        if (rid < 0 || rid >= REGION_COUNT) {
            continue;
        }

        // 累加权重和加权偏移
        int w = weights[rid];
        sum_w += w;
        sum_wdx += w * (cx - img_center_x);
    }

    // 5. 计算最终偏移量 dx
    int dx = 0;
    if (sum_w > 0) {
        dx = (int)(sum_wdx / sum_w);
    }

    // 6. 构造返回值：(blob_count, dx)
    mp_obj_t res_tuple[2];
    res_tuple[0] = mp_obj_new_int(blob_cnt);
    res_tuple[1] = mp_obj_new_int(dx);

    return mp_obj_new_tuple(2, res_tuple);
}
static MP_DEFINE_CONST_FUN_OBJ_KW(track_TrackImage_find_offset_obj, 1, track_TrackImage_find_offset);

// 定义数组并作为类的字典，其内包含类所有方法和其它静态属性
static const mp_rom_map_elem_t track_TrackImage_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_deinit), MP_ROM_PTR(&track_TrackImage_deinit_obj) },
    { MP_ROM_QSTR(MP_QSTR_update_image), MP_ROM_PTR(&track_TrackImage_update_image_obj) },
    { MP_ROM_QSTR(MP_QSTR_buffer), MP_ROM_PTR(&track_TrackImage_buffer_obj) },
    { MP_ROM_QSTR(MP_QSTR_find_blobs), MP_ROM_PTR(&track_TrackImage_find_blobs_obj) },      
    { MP_ROM_QSTR(MP_QSTR_find_offset), MP_ROM_PTR(&track_TrackImage_find_offset_obj) },
   
};
static MP_DEFINE_CONST_DICT(track_TrackImage_locals_dict, track_TrackImage_locals_dict_table);

// TrackImage类的类型定义
MP_DEFINE_CONST_OBJ_TYPE(                     // 定义类的顶级宏
    track_type_TrackImage,                    // 参数1：C语言层面类名
    MP_QSTR_TrackImage,                       // 参数2：Python层面类名
    MP_TYPE_FLAG_NONE,                        // 参数3：类型标志位。
    make_new, track_TrackImage_make_new,      // 参数4、5：键值对，定义构造函数
    locals_dict, &track_TrackImage_locals_dict// 参数6、7：键值对，定义包含类方法的字典
);



// ================================ 第5部分：模块注册 ================================
// 定义模块全局表，包含模块所有属性
static const mp_rom_map_elem_t track_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_track) },
    { MP_ROM_QSTR(MP_QSTR_TrackImage), MP_ROM_PTR(&track_type_TrackImage) },
};
static MP_DEFINE_CONST_DICT(track_module_globals, track_module_globals_table);
// 定义模块对象
const mp_obj_module_t track_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&track_module_globals,
};
// 注册模块
MP_REGISTER_MODULE(MP_QSTR_track, track_user_cmodule);