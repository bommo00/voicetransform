import flet as ft
import boto3
from botocore.exceptions import NoCredentialsError
import uuid
import os
import flet_fastapi

# Initiate the connection with s3 and polly
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_default_region = os.getenv('AWS_DEFAULT_REGION')
bucket = os.getenv('BUCKET')

polly_client = boto3.client('polly',
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key,
                            region_name=aws_default_region
                            )

s3_client = boto3.client('s3',
                         aws_access_key_id=aws_access_key_id,
                         aws_secret_access_key=aws_secret_access_key,
                         region_name=aws_default_region
                         )

# Dictionary for the voice choosing
voice = {'日本語': {'female': 'Kazuha', 'male': 'Takumi'},
         '英語 (米国)': {'female': 'Danielle', 'male': 'Joey'},
         '英語 (オーストラリア)': {'female': 'Olivia', 'male': 'None'},
         '英語 (英国)': {'female': 'Amy', 'male': 'Arthur'},
         '韓国語': {'female': 'Seoyeon', 'male': 'None'},
         '標準中国語': {'female': 'Zhiyu', 'male': 'None'},
         '中国語 (広東語)': {'female': 'Hiujin', 'male': 'None'},
         'アラビア語 (湾岸)': {'female': 'Hala', 'male': 'Zayd'},
         'ベルギーオランダ語 (フランドル語)': {'female': 'Lisa', 'male': 'None'},
         'カタロニア語': {'female': 'Arlet', 'male': 'None'},
         'デンマーク語': {'female': 'Sofie', 'male': 'None'},
         'オランダ語': {'female': 'Laura', 'male': 'None'},
         'フィンランド語': {'female': 'Suvi', 'male': 'None'},
         'フランス語 (カナダ)': {'female': 'Gabrielle', 'male': 'Liam'},
         'フランス語': {'female': 'Léa', 'male': 'Rémi'},
         'ドイツ語': {'female': 'Vicki', 'male': 'Daniel'},
         'ヒンディー語': {'female': 'Kajal', 'male': 'None'},
         'イタリア語': {'female': 'Bianca', 'male': 'Adriano'},
         'ノルウェー語': {'female': 'Ida', 'male': 'None'},
         'ポーランド語': {'female': 'Ola', 'male': 'None'},
         'ポルトガル語 (欧州)': {'female': 'Camila', 'male': 'Thiago'},
         'スペイン語 (欧州)': {'female': 'Lucia', 'male': 'Sergio'},
         'スペイン語 (メキシコ)': {'female': 'Mia', 'male': 'Andrés'},
         'スウェーデン語': {'female': 'Elin', 'male': 'None'},
         }


# Generate the audio from text
def reading(text, vo):
    # Get the output audio data
    response = polly_client.synthesize_speech(
        Engine="neural",
        OutputFormat='mp3',
        SampleRate='8000',
        Text=text,
        TextType='text',
        VoiceId=vo,
    )
    voice = response['AudioStream'].read()

    # Upload the audio data to S3
    key = 'voice/' + str(uuid.uuid4()) + '.mp3'
    try:
        s3_client.put_object(Bucket=bucket, Key=key, Body=voice)
    except NoCredentialsError:
        return False
    # Generate the download url
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket,
                                                            'Key': key},
                                                    ExpiresIn=600)
    except NoCredentialsError:
        return False

    return [key, response]


# Delete the temp file when the user closes the page
# def delete_file_from_s3(key):
#     try:
#         s3_client.delete_object(Bucket=bucket, Key=key)
#     except NoCredentialsError:
#         return None


# Main page building
async def main(page: ft.Page):
    # Change GUI by language choice ***Some languages only have female voice
    async def choice_change(e):
        if voice[language.value]['male'] == 'None':
            if len(choose.controls) > 1:
                choose.controls.pop()
                gender.value = 'female'
        else:
            if len(choose.controls) == 1:
                choose.controls.append(ft.Radio(value="male", label="男性の声", active_color='WHITE'))
        await page.update_async()

    async def download_voice(_):
        await page.launch_url_async(url)

    # Generate audio and change the GUI from the response
    async def transform(_):
        # Play the audio by button
        async def play_audio(e):
            if play_button.data:
                play_button.data = 0
                await audio.pause_async()
                play_button.icon = ft.icons.PLAY_ARROW
            else:
                play_button.data = 1
                await audio.resume_async()
                play_button.icon = ft.icons.PAUSE
            await page.update_async()

        # Release the audio if here is something playing
        global audio
        if audio:
            await audio.release_async()

        # Generate the audio by the input content and configuration
        if content.value:
            data = reading(content.value, voice[language.value][gender.value])
        else:
            data = reading('テキストを入力してください', 'Kazuha')

        # Append button for the audio playing and download
        if data:
            global key, url
            key = data[0]
            url = data[1]
            audio = ft.Audio(
                src=url,
                autoplay=False,
                volume=1,
                balance=0,

            )
            # First time to play
            if len(page.overlay) == 0:
                page.overlay.append(audio)
                play_button = ft.IconButton(ft.icons.PLAY_ARROW, icon_size=50, icon_color=ft.colors.WHITE, data=0,
                                            on_click=play_audio)
                page.add(ft.Row(
                    [
                     ft.IconButton(ft.icons.DOWNLOADING_ROUNDED, icon_size=50, icon_color=ft.colors.WHITE,
                                   on_click=download_voice),
                     ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                    ft.Text('フレームワークの制約により、ウェブバージョンでは音声の再生機能が無効化されています'),
                    ft.TextButton('音声再生機能をつけているDesktop APP ver. はこちら： https://github.com/bommo00/voicetransform',
                                  on_click=lambda _: page.launch_url_async('https://github.com/bommo00/voicetransform'))
                )
            else:
                # Change the audio
                page.overlay.append(audio)

        else:
            page.controls.append(ft.Text('音声化に失敗しました。もう一度やり直してください…'))
        await page.update_async()

    # Build the main GUI
    page.title = "読み上げます"
    page.vertical_alignment = ft.MainAxisAlignment.SPACE_AROUND
    page.padding = 70
    page.bgcolor = ft.colors.LIME
    page.scroll = True

    choose = ft.Row([
        ft.Radio(value="female", label="女性の声", active_color='WHITE', ),
        ft.Radio(value="male", label="男性の声", active_color='WHITE')])
    gender = ft.RadioGroup(content=choose, value="female")

    language = ft.Dropdown(
        width=250,
        border_color='WHITE',
        options=[ft.dropdown.Option(v) for v in voice],
        on_change=choice_change,
        value='日本語',
    )

    content = ft.TextField(hint_text="ここにテキストを入力してください",
                           width=650,
                           multiline=True,
                           border_color='WHITE',
                           bgcolor='WHITE',
                           expand=True
                           )
    await page.add_async(
        ft.Row(
            [
                ft.Text('音声化ツール', size=60, text_align=ft.TextAlign.LEFT, height=100, font_family="Kanit",
                        color="WHITE"),
                gender,
                language,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        ft.Row(
            [content,
             ft.IconButton(ft.icons.SWITCH_ACCESS_SHORTCUT_ROUNDED, icon_size=50, icon_color=ft.colors.LIME_200,
                           selected_icon_color=ft.colors.WHITE, on_click=transform),
             ],
            vertical_alignment=ft.CrossAxisAlignment.END,
            alignment=ft.MainAxisAlignment.START,
        )
        ,
    )
    await page.update_async()
    # initialize audio
    global audio
    audio = None



app = flet_fastapi.app(main)