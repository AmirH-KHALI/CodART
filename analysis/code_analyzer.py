import os

from antlr4 import *
from antlr4.TokenStreamRewriter import TokenStreamRewriter

from gen.java.JavaLexer import JavaLexer
from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled
from gen.javaLabeled.JavaParserLabeledListener import JavaParserLabeledListener


def get_java_files(directory):
    if not os.path.isdir(directory):
        raise ValueError("directory should be an absolute path of a directory!")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.split('.')[-1] == 'java':
                yield os.path.join(root, file), file


class CodeAnalyzerListener(JavaParserLabeledListener):

    def __init__(self, common_token_stream: CommonTokenStream = None):

        if common_token_stream is None:
            raise ValueError("common_token_stream is None")
        else:
            self.token_stream_rewriter = TokenStreamRewriter(common_token_stream)

        self.class_num = 0
        self.current_class_name = None
        self.method_nums = dict()
        self.public_attr_nums = dict()
        self.private_attr_nums = dict()

        self.TAB = "\t"
        self.NEW_LINE = "\n"
        self.code = ""

    def enterClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        self.class_num += 1

        self.current_class_name = ctx.IDENTIFIER().getText()
        self.method_nums[self.current_class_name] = 0
        self.public_attr_nums[self.current_class_name] = 0
        self.private_attr_nums[self.current_class_name] = 0

    def exitClassDeclaration(self, ctx: JavaParserLabeled.ClassDeclarationContext):
        self.current_class_name = None

    def enterMethodDeclaration(self, ctx: JavaParserLabeled.MethodDeclarationContext):
        if self.current_class_name is not None:
            self.method_nums[self.current_class_name] += 1

    def enterFieldDeclaration(self, ctx: JavaParserLabeled.FieldDeclarationContext):
        if self.current_class_name is not None:
            class_body_declaration = ctx.parentCtx.parentCtx

            if len(class_body_declaration.modifier()) > 0 \
                    and class_body_declaration.modifier()[0].getText() == 'private':
                self.private_attr_nums[self.current_class_name] += 1
            else:
                self.public_attr_nums[self.current_class_name] += 1


class CodeAnalyzerAPI:

    def __init__(self, file_path):
        self.file_path = file_path
        self.stream = FileStream(self.file_path, encoding="utf8")
        self.lexer = JavaLexer(self.stream)
        self.token_stream = CommonTokenStream(self.lexer)
        self.parser = JavaParserLabeled(self.token_stream)
        self.tree = self.parser.compilationUnit()
        self.walker = ParseTreeWalker()

    def do_analyse(self):
        listener = CodeAnalyzerListener(
            common_token_stream=self.token_stream
        )
        self.walker.walk(
            listener=listener,
            t=self.tree
        )

        return listener


if __name__ == '__main__':
    total_class_num = 0
    output = ''
    for f in get_java_files(
            "E:\\desk\\University\\99002-CD (compiler)\\Project\\CodART\\benchmark_projects\\JSON"
    ):
        listener = CodeAnalyzerAPI(f[0]).do_analyse()

        classes = list(listener.method_nums.keys())
        for i in range(len(classes)):
            class_name = classes[i]
            output += str(total_class_num + 1) + '.' + class_name + ':\n'
            output += listener.TAB + 'no.attrs: ' \
                      + str(listener.private_attr_nums[class_name] + listener.public_attr_nums[class_name]) + '\n'
            output += listener.TAB + listener.TAB + 'public: ' + str(listener.public_attr_nums[class_name]) + '\n'
            output += listener.TAB + listener.TAB + 'private: ' + str(listener.private_attr_nums[class_name]) + '\n'
            output += listener.TAB + 'no.methods: ' + str(listener.method_nums[class_name]) + '\n'
            total_class_num += 1

    print('no.classes:', str(total_class_num))
    print(output)

