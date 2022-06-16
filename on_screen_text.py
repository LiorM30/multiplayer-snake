import pygame

from enums import Color


class On_Screen_Input:
    def __init__(self, screen: pygame.Surface) -> None:
        self._screen = screen

        pygame.font.init()

        self._font = pygame.font.Font('freesansbold.ttf', 32)

    def get_input(
        self,
        length: int,
        color: Color,
        x: int, y: int,
        title_text: str,
        BG_color: Color
    ) -> str:
        complete_input = ''
        done = False
        while not done:
            rendered_input = self._font.render(
                complete_input, True,
                color.value, None
            )
            textRect = rendered_input.get_rect()
            textRect.center = (x, y)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return None

                if event.type == pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_a:
                            if len(complete_input) < length:
                                complete_input += 'A'
                        case pygame.K_b:
                            if len(complete_input) < length:
                                complete_input += 'B'
                        case pygame.K_c:
                            if len(complete_input) < length:
                                complete_input += 'C'
                        case pygame.K_d:
                            if len(complete_input) < length:
                                complete_input += 'D'
                        case pygame.K_e:
                            if len(complete_input) < length:
                                complete_input += 'E'
                        case pygame.K_f:
                            if len(complete_input) < length:
                                complete_input += 'F'
                        case pygame.K_g:
                            if len(complete_input) < length:
                                complete_input += 'G'
                        case pygame.K_h:
                            if len(complete_input) < length:
                                complete_input += 'H'
                        case pygame.K_i:
                            if len(complete_input) < length:
                                complete_input += 'I'
                        case pygame.K_j:
                            if len(complete_input) < length:
                                complete_input += 'J'
                        case pygame.K_k:
                            if len(complete_input) < length:
                                complete_input += 'K'
                        case pygame.K_l:
                            if len(complete_input) < length:
                                complete_input += 'L'
                        case pygame.K_m:
                            if len(complete_input) < length:
                                complete_input += 'M'
                        case pygame.K_n:
                            if len(complete_input) < length:
                                complete_input += 'N'
                        case pygame.K_o:
                            if len(complete_input) < length:
                                complete_input += 'O'
                        case pygame.K_p:
                            if len(complete_input) < length:
                                complete_input += 'P'
                        case pygame.K_q:
                            if len(complete_input) < length:
                                complete_input += 'Q'
                        case pygame.K_r:
                            if len(complete_input) < length:
                                complete_input += 'R'
                        case pygame.K_s:
                            if len(complete_input) < length:
                                complete_input += 'S'
                        case pygame.K_t:
                            if len(complete_input) < length:
                                complete_input += 'T'
                        case pygame.K_u:
                            if len(complete_input) < length:
                                complete_input += 'U'
                        case pygame.K_v:
                            if len(complete_input) < length:
                                complete_input += 'V'
                        case pygame.K_w:
                            if len(complete_input) < length:
                                complete_input += 'W'
                        case pygame.K_x:
                            if len(complete_input) < length:
                                complete_input += 'X'
                        case pygame.K_y:
                            if len(complete_input) < length:
                                complete_input += 'Y'
                        case pygame.K_z:
                            if len(complete_input) < length:
                                complete_input += 'Z'
                        case pygame.K_BACKSPACE:
                            complete_input = complete_input[:-1]
                        case pygame.K_RETURN:
                            done = True
            self._screen.fill(BG_color.value)
            if title_text:
                self.render_text(title_text, color, x, y - 10)
            self._screen.blit(rendered_input, textRect)

            pygame.display.flip()
        return complete_input

    def render_text(self, message: str, color: Color, x: int, y: int) -> None:
        rendered_text = self._font.render(
            message, True,
            color.value, None
        )
        text_rect = rendered_text.get_rect()
        text_rect.center = (x, y)
        self._screen.blit(rendered_text, rendered_text.get_rect())
