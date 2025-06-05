ROOK_MAGIC = [
    0x8A80104000800020, 0x0140002000100040, 0x02801880A0017001,
    0x0100081001000420, 0x0200020010080420, 0x03001C0002010008,
    0x0848000800200010, 0x0208008800440290,
    0x0008000982040000, 0x0202440100020004, 0x0010080200080100,
    0x0120800800801000, 0x0208808088000400, 0x0280220080040000,
    0x0220080010002008, 0x0801000060821100,
    0x0800440064220000, 0x0010080802000400, 0x0121080A00102042,
    0x0140848010000802, 0x0481828014002800, 0x0809400400200410,
    0x0401004001001082, 0x0002000088061040,
    0x0100400080208000, 0x0204000212008100, 0x0212006801000081,
    0x0201000800800080, 0x02000A0020040100, 0x0002008080040000,
    0x0800884001001020, 0x0800046000428810,
    0x0404000804080002, 0x0440003000200801, 0x0420001100450000,
    0x0188020010100100, 0x0148004018028000, 0x0208004008080020,
    0x0124080204001001, 0x0200046502000484, 0x0480400080088020,
    0x0100042201003400, 0x0302001001100040, 0x0001000210100009,
    0x0200208010011004, 0x0202008004008002, 0x0200200040101000,
    0x0204844004082001, 0x0101002200408200, 0x0408020004010800,
    0x0400814200441010, 0x02060820C0120200, 0x0001001004080100,
    0x020C020080040080, 0x0293561083002240, 0x0444400410092000,
    0x0280001040802101, 0x0210019004000208, 0x080C008410010200,
    0x0402408100100042, 0x00020030A0244872, 0x0001200100841440,
    0x02006104900A0804, 0x0001004081002402,
]

BISHOP_MAGIC = [
    0x0040040844404084, 0x002004208A004208, 0x0010190041080202,
    0x0108060845042010, 0x0581104180800210, 0x0211208044620001,
    0x0108082082006021, 0x03C0808410220200,
    0x0004050404440404, 0x0000210014200880, 0x024D008080108210,
    0x0001020A0A020400, 0x0004030820004020, 0x0004011002100800,
    0x0004014841041040, 0x0008010104020202,
    0x00400210C3880100, 0x0040402202410820, 0x0008100182002041,
    0x0004002801A02003, 0x0008504082008040, 0x000810102C808880,
    0x0000E90041088480, 0x0008002020480840,
    0x0220200865090201, 0x002010100A020212, 0x0015204840802240,
    0x0002008000208111, 0x0002008610040200, 0x0004804400A0300C,
    0x0000400400410200, 0x0010008040010040,
    0x0044104003501040, 0x0040011A04055100, 0x0004081004C02040,
    0x0040410409000B00, 0x0080801040800000, 0x0001010001040003,
    0x0000401844410000, 0x0002002010484040, 0x0001001048008020,
    0x0004082008080000, 0x00000000200B0400, 0x0000000020181020,
    0x0000020004081820, 0x0002004100040080, 0x0000810200020004,
    0x0000801046008020, 0x0000001020481000, 0x00000030020C0804,
    0x0000001802060080, 0x0006000C01226100, 0x0000010003014400,
    0x000800A600360100, 0x0001000400420000,  # ←-- fixed (was “p000”)
    0x0004010040041000, 0x0000400080100080, 0x0040002040002000,
    0x0000100800200080, 0x0000020080400080, 0x0000100204000200,
    0x0000010080200080, 0x0000200040080010, 0x0000800080010000,
]



def precompute_king_attacks(position):
    row = position // 8
    col = position % 8
    mask = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            if 0 <= row + i < 8 and 0 <= col + j < 8 and not (i == 0 and j == 0):
                mask |= 1 << (row + i) * 8 + (col + j)

    return mask


def precompute_knight_attacks(position):
    row = position // 8
    col = position % 8
    mask = 0
    for i in range(-2, 3):
        if i == 2 or i == -2:
            for j in (1, -1):
                if 0 <= row + i < 8 and 0 <= col + j < 8:
                    mask |= 1 << (row + i) * 8 + (col + j)
        elif i == 1 or i == -1:
            for j in (2, -2):
                if 0 <= row + i < 8 and 0 <= col + j < 8:
                    mask |= 1 << (row + i) * 8 + (col + j)
    return mask


def precompute_pawn_attacks(position):
    row = position // 8
    col = position % 8
    mask = 0
    if row < 7:
        if col + 1 < 8:
            mask |= 1 << (row + 1) * 8 + (col + 1)
        if col - 1 >= 0:
            mask |= 1 << (row + 1) * 8 + (col-1)

    return mask

def get_magic_index(occ, magic_number, shift):
    result = (occ * magic_number) & 0xFFFFFFFFFFFFFFFF
    if shift:
        result >> (64 - shift)
    return result

def count_ones_kernighan(n):
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count

def precompute_rook_attacks(position):
    row = position // 8
    col = position % 8

    
    up_dict = {0:0}
    down_dict = {0:0}
    left_dict = {0:0}
    right_dict = {0:0}
    up_bits = max(7- row -1, 0)
    down_bits = max(row - 1, 0)
    right_bits = max(7 - col -1, 0)
    left_bits = max(col - 1, 0)
    bit_shift = up_bits + down_bits + left_bits + right_bits
    
    result: list = [0] * (1 << bit_shift)
    
    # calculate for top here
    for i in range(0, 2**up_bits):
        occ_bb = 0
        temp_result = 0
        is_blocked = False
        if i == 0:
            for k in range(row + 1, 8):
                temp_result |= 1 << k*8 + col
            up_dict[0x0000000000000000] = temp_result
            continue
        elif row < 6:
            for k in range(row+1, 7):
                
                lsb = i & 1
                i = i >> 1
                if lsb == 1:
                    occ_bb |= 1 << k*8 + col
                    if not is_blocked:
                        is_blocked = True
                        for j in range(row + 1, k+1):
                            temp_result |= 1 << j*8 + col
            up_dict[occ_bb] = temp_result
    
    for key, value in up_dict.items():
        print(bin(key), bin(value))
           
           
    # calculate for down here
    for i in range(0, 2**down_bits):
        occ_bb = 0
        temp_result = 0
        is_blocked = False
        if i == 0:
            for k in range(0, row):
                temp_result |= 1 << k*8 + col
            down_dict[0x0000000000000000] = temp_result
            continue
        elif row > 1:
            for k in range(row-1, 0, -1):
                lsb = i & 1
                i = i >> 1
                if lsb == 1:
                    occ_bb |= 1 << k*8 + col
                    if not is_blocked:
                        is_blocked = True
                        for j in range(row -1, k-1, -1):
                            temp_result |= 1 << j*8 + col
            down_dict[occ_bb] = temp_result
    
    # for key, value in down_dict.items():
    #     print(bin(key), bin(value))
        
        
    # calculate for left here
    for i in range(0, 2**left_bits):
        occ_bb = 0
        temp_result = 0
        is_blocked = False
        if i == 0:
            for k in range(0, col):
                temp_result |= 1 << row*8 + k
            left_dict[0x0000000000000000] = temp_result
            continue
        elif col > 1:
            for k in range(col-1, 0, -1):
                lsb = i & 1
                i = i >> 1
                if lsb == 1:
                    occ_bb |= 1 << row*8 + k
                    if not is_blocked:
                        is_blocked = True
                        for j in range(col -1, k-1, -1):
                            temp_result |= 1 << row*8 + j
            left_dict[occ_bb] = temp_result
    
    
    # for key, value in left_dict.items():
    #     print(bin(key), bin(value))
        
        
    # calculate for right here
    for i in range(0, 2**right_bits):
        occ_bb = 0
        
        temp_result = 0
        is_blocked = False
        if i == 0:
            for k in range(col + 1, 8):
                temp_result |= 1 << row*8 + k
            right_dict[0x0000000000000000] = temp_result
            continue
        elif col < 6:
            for k in range(col+1, 7):
                lsb = i & 1
                i = i >> 1
                if lsb == 1:
                    occ_bb |= 1 << row*8 + k
                    if not is_blocked:
                        is_blocked = True
                        for j in range(col + 1, k+1):
                            temp_result |= 1 << row*8 + j
            right_dict[occ_bb] = temp_result
    
    # for key, value in right_dict.items():
    #     print(bin(key), bin(value))
        
    
    for u_key, u_value in up_dict.items():
        for d_key, d_value in down_dict.items():
            for r_key, r_value in right_dict.items():
                for l_key, l_value in left_dict.items():   
                    occ_bb = u_key | d_key | r_key | l_key
                    magic_index = get_magic_index(occ_bb, ROOK_MAGIC[position], bit_shift)     
                    result[magic_index] = u_value | d_value | r_value | l_value
    
    
        
    return result
                


if __name__ == '__main__':
    precompute_rook_attacks(48)
    
