from unittest import TestCase
import os
import sys
import time
from shutil import rmtree
from subprocess import Popen, PIPE
from zipfile import ZipFile
from beagles.io.flags import SharedFlagIO
from beagles.base import BACKEND_ENTRYPOINT


class TestBackend(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        open('tests/resources/checkpoint', 'w').close()
        with ZipFile('tests/resources/BCCD.v1-resize-416x416.voc.zip', 'r') as f:
            f.extractall('tests/resources/BCCD')
        time.sleep(5)

    def setUp(self):
        self.io = SharedFlagIO(subprogram=False)
        self.flags = self.io.flags

    def testBackendWrapperYoloV2(self):
        self.flags.model = 'tests/resources/yolov2-lite-3c.cfg'
        self.flags.dataset = 'tests/resources/BCCD/train'
        self.flags.labels = 'tests/resources/BCCD.classes'
        self.flags.annotation = 'tests/resources/BCCD/train'
        self.flags.backup = 'tests/resources/ckpt'
        self.flags.project_name = '_test'
        self.flags.trainer = 'adam'
        self.flags.lr = 0.00001
        self.flags.max_lr = 0.0001
        self.flags.step_size_coefficient = 10
        self.flags.load = 0
        self.flags.batch = 4
        self.flags.epoch = 1
        self.flags.train = True
        self.io.io_flags()
        proc = Popen([sys.executable, BACKEND_ENTRYPOINT], stdout=PIPE, shell=False)
        proc.communicate()
        self.assertEqual(proc.returncode, 0)
        self.flags.load = 1
        self.io.io_flags()
        proc = Popen([sys.executable, BACKEND_ENTRYPOINT], stdout=PIPE, shell=False)
        proc.communicate()
        self.flags.train = False
        self.flags.imgdir = 'tests/resources/BCCD/test'
        self.io.io_flags()
        proc = Popen([sys.executable, BACKEND_ENTRYPOINT], stdout=PIPE, shell=False)
        proc.communicate()
        self.flags.video = ['tests/resources/test.mp4']
        self.io.io_flags()
        proc = Popen([sys.executable, BACKEND_ENTRYPOINT], stdout=PIPE, shell=False)
        proc.communicate()
        self.assertEqual(proc.returncode, 0)

    def testBackendGradientExplosion(self):
        self.flags.model = 'tests/resources/yolov2-lite-3c.cfg'
        self.flags.dataset = 'tests/resources/BCCD/train'
        self.flags.labels = 'tests/resources/BCCD.classes'
        self.flags.annotation = 'tests/resources/BCCD/train'
        self.flags.backup = 'tests/resources/ckpt'
        self.flags.project_name = '_test'
        self.flags.trainer = 'adam'
        self.flags.lr = 100000000.0
        self.flags.max_lr = 100000000.0
        self.flags.load = 0
        self.flags.batch = 4
        self.flags.epoch = 1
        self.flags.train = True
        self.io.io_flags()
        proc = Popen([sys.executable, BACKEND_ENTRYPOINT], stdout=PIPE, shell=False)
        proc.communicate()
        self.assertNotEqual(proc.returncode, 0)

    def tearDown(self) -> None:
        self.io.cleanup_flags()

    @classmethod
    def tearDownClass(cls):
        for f in os.listdir('tests/resources/ckpt'):
            if f.endswith(('.data-00000-of-00001', '.index', '.meta', '.profile')):
                f = os.path.join('tests/resources/ckpt', f)
                os.remove(f)
        os.remove('tests/resources/ckpt/checkpoint')
        rmtree('tests/resources/BCCD')
        try:
            rmtree('data/summaries/_test')
        except FileNotFoundError:
            pass
